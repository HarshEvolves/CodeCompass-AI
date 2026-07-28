import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await api.get<UserProfile>("/auth/me");
        setProfile(response.data);
      } catch (err: any) {
        setError("Session expired or invalid token.");
        localStorage.removeItem("access_token");
        navigate("/login");
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-accent border-t-transparent rounded-full animate-spin" />
          <span className="text-text-secondary text-sm">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      {/* Navbar header */}
      <header className="border-b border-border-default bg-bg-secondary/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">🧭</span>
            <span className="font-bold tracking-tight text-xl gradient-text">
              CodeCompass
            </span>
          </div>

          <div className="flex items-center gap-4">
            {profile && (
              <span className="text-sm text-text-secondary">
                Hello, <strong className="text-text-primary">{profile.full_name}</strong>
              </span>
            )}
            <button
              onClick={handleLogout}
              className="px-4 py-2 border border-border-default hover:border-error hover:text-error rounded-lg text-sm transition-colors duration-200 cursor-pointer"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main dashboard content area */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="glass-card p-8 mb-8 text-left relative overflow-hidden">
          {/* Decorative ambient background */}
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full bg-accent opacity-5 blur-3xl pointer-events-none" />

          <h2 className="text-3xl font-bold mb-3">Dashboard</h2>
          <p className="text-text-secondary text-sm max-w-xl">
            You have successfully authenticated! This is a placeholder dashboard.
            Future repository uploading and RAG AI components will be added in later commits.
          </p>
        </div>

        {profile && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="glass-card p-6 text-left">
              <h3 className="text-lg font-semibold mb-4 text-text-secondary border-b border-border-default/50 pb-2">
                User Profile Info
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center py-1">
                  <span className="text-text-secondary text-sm">Full Name</span>
                  <span className="text-sm font-medium">{profile.full_name}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-t border-border-default/20">
                  <span className="text-text-secondary text-sm">Email Address</span>
                  <span className="text-sm font-medium font-mono">{profile.email}</span>
                </div>
                <div className="flex justify-between items-center py-1 border-t border-border-default/20">
                  <span className="text-text-secondary text-sm">User UUID ID</span>
                  <span className="text-xs font-mono text-text-secondary bg-bg-secondary px-2 py-1 rounded">
                    {profile.id}
                  </span>
                </div>
              </div>
            </div>

            <div className="glass-card p-6 text-left border border-dashed border-border-default/80 flex flex-col justify-center items-center text-center">
              <span className="text-4xl mb-3">📁</span>
              <h4 className="font-semibold mb-1 text-text-secondary">No Repositories Uploaded</h4>
              <p className="text-xs text-text-muted max-w-xs">
                In Phase 9+, you will be able to upload ZIP files of codebases and query them using RAG.
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
