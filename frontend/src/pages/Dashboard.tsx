import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "@/lib/axios";
import LoadingSpinner from "@/components/LoadingSpinner";
import UploadZone from "@/components/UploadZone";
import RepositoryCard from "@/components/RepositoryCard";

interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
}

interface Repository {
  id: string;
  name: string;
  original_filename: string;
  upload_status: string;
  created_at: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [loadingRepos, setLoadingRepos] = useState(true);

  const fetchProfile = async () => {
    try {
      const response = await api.get<UserProfile>("/auth/me");
      setProfile(response.data);
    } catch (err: any) {
      localStorage.removeItem("access_token");
      navigate("/login");
    } finally {
      setLoadingProfile(false);
    }
  };

  const fetchRepositories = async () => {
    try {
      const response = await api.get<Repository[]>("/repositories");
      setRepositories(response.data);
    } catch (err: any) {
      console.error("Failed to load repositories:", err);
    } finally {
      setLoadingRepos(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchRepositories();
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    navigate("/login");
  };

  if (loadingProfile) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <LoadingSpinner message="Loading dashboard profile..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      {/* Header section */}
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
              className="px-4 py-2 border border-border-default hover:border-error hover:text-error rounded-lg text-sm transition-colors duration-200 cursor-pointer font-semibold"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main dashboard content area */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left panel: Profile info & Upload Area */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* User Profile Card */}
            {profile && (
              <div className="glass-card p-6 text-left relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-accent opacity-5 blur-2xl pointer-events-none" />
                <h3 className="text-lg font-bold mb-4 text-text-primary border-b border-border-default/50 pb-2 flex items-center gap-2">
                  <span>👤</span> Profile Information
                </h3>
                <div className="space-y-3.5">
                  <div className="flex flex-col">
                    <span className="text-text-secondary text-[11px] uppercase tracking-wider">Full Name</span>
                    <span className="text-sm font-medium text-text-primary">{profile.full_name}</span>
                  </div>
                  <div className="flex flex-col border-t border-border-default/10 pt-2.5">
                    <span className="text-text-secondary text-[11px] uppercase tracking-wider">Email Address</span>
                    <span className="text-sm font-mono text-text-primary truncate" title={profile.email}>
                      {profile.email}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Upload Zone Component */}
            <div className="glass-card p-6 text-left">
              <h3 className="text-lg font-bold mb-4 text-text-primary border-b border-border-default/50 pb-2 flex items-center gap-2">
                <span>📤</span> Upload ZIP Repository
              </h3>
              <UploadZone onUploadSuccess={fetchRepositories} />
            </div>

          </div>

          {/* Right panel: Repository Grid list */}
          <div className="lg:col-span-2 space-y-6">
            <div className="glass-card p-6 flex justify-between items-center">
              <div>
                <h2 className="text-xl font-bold text-text-primary">Your Repositories</h2>
                <p className="text-xs text-text-secondary mt-0.5">
                  Manage extraction, code-structure parsing, line chunking, and ChromaDB indexing.
                </p>
              </div>
              <button
                onClick={fetchRepositories}
                disabled={loadingRepos}
                className="p-2 border border-border-default hover:bg-bg-secondary hover:border-accent text-sm rounded-lg transition-colors cursor-pointer"
                title="Refresh List"
              >
                🔄
              </button>
            </div>

            {loadingRepos ? (
              <div className="py-20">
                <LoadingSpinner message="Loading repositories..." />
              </div>
            ) : repositories.length === 0 ? (
              <div className="glass-card py-20 text-center flex flex-col justify-center items-center">
                <span className="text-5xl mb-4">🗂️</span>
                <h3 className="text-lg font-bold text-text-primary mb-1">No repositories found</h3>
                <p className="text-sm text-text-secondary max-w-sm">
                  Get started by dragging and dropping a ZIP file of your codebase into the upload area on the left.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {repositories.map((repo) => (
                  <RepositoryCard
                    key={repo.id}
                    repo={repo}
                    onActionSuccess={fetchRepositories}
                  />
                ))}
              </div>
            )}

          </div>

        </div>
      </main>
    </div>
  );
}
