import time
import httpx
from sqlalchemy.orm import Session
from app.models.api_log import ApiLog
from app.models.replay import Replay

class ReplayService:
    """
    Service layer executing async request dispatching and logging results in postgres.
    """
    
    @staticmethod
    async def trigger_replay(db: Session, log: ApiLog) -> Replay:
        """
        Asynchronously sends the identical stored HTTP request again using httpx.AsyncClient.
        Records response body, status, headers, and time in database.
        Catches connection, protocol, timeout, and dns failures gracefully without crashing.
        """
        method = log.method.upper()
        url = log.url
        headers = log.request_headers or {}
        body = log.request_body

        # Measure latency
        start_time = time.time()
        replay_success = False
        status_code = None
        resp_headers = None
        resp_body = None
        error_msg = None

        try:
            # Set a standard timeout limit to prevent hanging transactions
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Perform the HTTP call matching request parameters
                if body is not None:
                    response = await client.request(method, url, headers=headers, json=body)
                else:
                    response = await client.request(method, url, headers=headers)
            
            latency_ms = int((time.time() - start_time) * 1000)
            status_code = response.status_code
            resp_headers = dict(response.headers)
            
            # Attempt to parse response payload as JSON
            try:
                resp_body = response.json()
            except Exception:
                # Fallback to dictionary containing raw text if response body is not JSON
                resp_body = {"raw_text": response.text}
            
            replay_success = True

        except httpx.ConnectTimeout as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Connection Timeout: {str(e)}"
        except httpx.ReadTimeout as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Read Timeout: {str(e)}"
        except httpx.ConnectError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Connection Failure/Refused or DNS Error: {str(e)}"
        except httpx.UnsupportedProtocol as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Invalid URL/Unsupported Protocol: {str(e)}"
        except httpx.HTTPError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"HTTP request failed: {str(e)}"
        except (ValueError, Exception) as e:
            # Fallback for invalid URLs and unexpected runtime issues
            latency_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Error during replay request: {str(e)}"

        # Save results in the database
        replay_record = Replay(
            api_log_id=log.id,
            replay_status_code=status_code,
            replay_response_headers=resp_headers,
            replay_response_body=resp_body,
            replay_response_time_ms=latency_ms if replay_success else None,
            replay_success=replay_success,
            error_message=error_msg
        )
        db.add(replay_record)
        db.commit()
        db.refresh(replay_record)

        return replay_record
