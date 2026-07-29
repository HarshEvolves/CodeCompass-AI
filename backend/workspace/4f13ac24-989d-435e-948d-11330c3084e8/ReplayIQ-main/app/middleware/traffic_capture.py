import time
import json
import jwt
import uuid
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.models.api_request import APIRequest

class TrafficCaptureMiddleware(BaseHTTPMiddleware):
    """
    Middleware that captures incoming HTTP request and outgoing response payloads.
    Associates the traffic with the authenticated user's project.
    Excludes public, status, and static endpoints from logging.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Skip capture for documentation, health, and static asset routes
        path = request.url.path
        if (
            path.startswith("/docs")
            or path.startswith("/redoc")
            or path.startswith("/openapi.json")
            or path.startswith("/health")
            or path.startswith("/static")
            or path.startswith("/api/v1/auth")
        ):
            return await call_next(request)

        # 2. Authenticate the request via Authorization: Bearer token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            # Let it pass without logging; downstream route dependencies will handle 401
            return await call_next(request)

        token = auth_header.split(" ")[1]
        
        # Check if running in a test environment with an overridden session in app state
        is_test_env = hasattr(request.app.state, "db_session")
        if is_test_env:
            db = request.app.state.db_session
        else:
            db = SessionLocal()

        # Determine if the route is a project management route
        is_projects_route = path.startswith("/api/v1/projects")
        is_project_creation = (path == "/api/v1/projects" and request.method == "POST")

        try:
            # Decode token to extract email
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if not email:
                if not is_test_env:
                    db.close()
                return await call_next(request)

            # Query the user from the database
            user = db.query(User).filter(User.email == email).first()
            if not user:
                if not is_test_env:
                    db.close()
                return await call_next(request)

            # Check if user has projects.
            # Skip this validation error check if the route is a project management route
            project_id = None
            if not user.projects:
                if not is_projects_route:
                    if not is_test_env:
                        db.close()
                    from app.core.error_codes import ErrorCode
                    from app.core.responses import build_error_response
                    return JSONResponse(
                        status_code=400,
                        content=build_error_response(
                            code=ErrorCode.VALIDATION_ERROR,
                            message="No project exists for the authenticated user. Please create a project first."
                        )
                    )
            else:
                project_id = user.projects[0].id

        except jwt.ExpiredSignatureError:
            # Token expired; let downstream routing raise the appropriate 401 exception
            if not is_test_env:
                db.close()
            return await call_next(request)
        except jwt.InvalidTokenError:
            # Invalid token; let downstream routing raise the appropriate 401 exception
            if not is_test_env:
                db.close()
            return await call_next(request)
        except Exception:
            # General fallback; let downstream handle authentication
            if not is_test_env:
                db.close()
            return await call_next(request)

        # 3. Intercept and cache the request body stream
        body_bytes = await request.body()
        async def receive():
            return {"type": "http.request", "body": body_bytes, "more_body": False}
        request._receive = receive

        request_body_str = None
        if body_bytes:
            try:
                request_body_str = body_bytes.decode("utf-8")
            except Exception:
                request_body_str = "[Binary Data]"

        # 4. Measure response latency
        start_time = time.time()
        
        # Execute downstream handlers and endpoint logic
        response = await call_next(request)
        
        latency_ms = (time.time() - start_time) * 1000

        # 5. Capture response body stream
        response_body_str = None
        try:
            chunks = []
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            response_body_bytes = b"".join(chunks)
            
            # Reconstruct response payload since the stream was consumed
            response = Response(
                content=response_body_bytes,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            if response_body_bytes:
                try:
                    response_body_str = response_body_bytes.decode("utf-8")
                except Exception:
                    response_body_str = "[Binary Data]"
        except Exception as e:
            response_body_str = f"[Error reading response body: {str(e)}]"

        # 6. Save the captured traffic log in PostgreSQL if a project can be associated
        # If it was a project creation request, try to extract the newly created project ID from response JSON
        if is_project_creation and response.status_code == 201 and response_body_str:
            try:
                resp_json = json.loads(response_body_str)
                project_id = uuid.UUID(resp_json["id"])
            except Exception:
                pass

        if project_id:
            try:
                req_headers = dict(request.headers)
                resp_headers = dict(response.headers)
                
                # Mask security credentials
                if "authorization" in req_headers:
                    req_headers["authorization"] = "Bearer [MASKED]"

                client_ip = request.client.host if request.client else None

                api_request_log = APIRequest(
                    project_id=project_id,
                    method=request.method,
                    path=path,
                    query_params=request.url.query,
                    request_headers=req_headers,
                    request_body=request_body_str,
                    response_status=response.status_code,
                    response_headers=resp_headers,
                    response_body=response_body_str,
                    response_time_ms=latency_ms,
                    client_ip=client_ip
                )
                db.add(api_request_log)
                db.commit()
            except Exception:
                db.rollback()
            finally:
                if not is_test_env:
                    db.close()
        else:
            if not is_test_env:
                db.close()

        return response
