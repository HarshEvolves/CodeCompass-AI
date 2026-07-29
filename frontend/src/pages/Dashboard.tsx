import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass,
  LogOut,
  Search,
  RefreshCw,
  FolderOpen,
  Database,
} from "lucide-react";
import api from "@/lib/axios";
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
  const [searchQuery, setSearchQuery] = useState("");

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
      setLoadingRepos(true);
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

  // Filter repositories based on search query
  const filteredRepos = repositories.filter((repo) =>
    repo.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalIndexed = repositories.filter((r) => r.upload_status.toUpperCase() === "INDEXED").length;

  if (loadingProfile) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-8 border-3 border-accent border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-semibold text-text-secondary">Verifying credentials...</span>
      </div>
    );
  }

  // Get initial for profile avatar
  const avatarInitial = profile?.full_name ? profile.full_name.charAt(0).toUpperCase() : "U";

  return (
    <div className="min-h-screen bg-bg-primary text-text-primary flex flex-col select-none font-sans">
      {/* Sticky top navbar */}
      <header className="sticky top-0 z-40 w-full border-b border-border-default bg-[#09090B]/85 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer select-none" onClick={() => navigate("/dashboard")}>
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center shadow-lg shadow-accent/20">
              <Compass className="w-5.5 h-5.5 text-white" />
            </div>
            <span className="font-bold tracking-tight text-base text-text-primary">
              CodeCompass <span className="text-accent">AI</span>
            </span>
          </div>

          {/* Search bar (Center) */}
          <div className="hidden md:flex flex-1 max-w-md relative select-text">
            <Search className="absolute left-4 top-3.5 w-4 h-4 text-text-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search codebases..."
              className="w-full pl-11 pr-4 py-2.5 bg-bg-secondary border border-border-default rounded-xl text-xs placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-2 focus:ring-accent-glow transition-all"
            />
          </div>

          {/* Profile controls (Right) */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-accent/20 border border-accent/35 flex items-center justify-center font-bold text-xs text-accent uppercase">
                {avatarInitial}
              </div>
              <div className="hidden sm:flex flex-col text-left">
                <span className="text-xs font-bold text-text-primary leading-none">
                  {profile?.full_name}
                </span>
                <span className="text-[10px] text-text-muted mt-1 font-mono select-all">
                  {profile?.email}
                </span>
              </div>
            </div>
            <span className="text-border-default">|</span>
            <button
              onClick={handleLogout}
              className="p-2.5 border border-border-default hover:border-error hover:text-error hover:bg-error/5 rounded-xl transition-all cursor-pointer"
              title="Sign Out"
            >
              <LogOut className="w-4.5 h-4.5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main dashboard content (Max Width Container, Generous spacing) */}
      <main className="max-w-7xl w-full mx-auto px-8 py-10 flex-1 flex flex-col lg:grid lg:grid-cols-12 gap-8">
        
        {/* Left column sidebar (col-span-4): Stats, Profile & Upload separated by gaps */}
        <div className="col-span-12 lg:col-span-4 space-y-6 flex flex-col justify-start">
          
          {/* User Profile Info Card */}
          {profile && (
            <div className="saas-card p-6 text-left relative overflow-hidden bg-bg-card border border-border-default rounded-2xl">
              <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-accent opacity-[0.03] blur-2xl pointer-events-none" />
              <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block mb-4">
                User Details
              </span>
              <div className="space-y-4">
                <div className="flex flex-col">
                  <span className="text-text-muted text-[10px] uppercase font-bold tracking-wider">Full Name</span>
                  <span className="text-sm font-semibold text-text-primary mt-1">{profile.full_name}</span>
                </div>
                <div className="flex flex-col border-t border-border-default pt-3">
                  <span className="text-text-muted text-[10px] uppercase font-bold tracking-wider">Email Address</span>
                  <span className="text-xs font-mono text-text-primary mt-1 truncate select-all" title={profile.email}>
                    {profile.email}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Dashboard Quick Stats */}
          <div className="saas-card p-6 text-left bg-bg-card border border-border-default rounded-2xl">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block mb-4">
              Workspace Overview
            </span>
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-bg-hover text-text-secondary">
                  <FolderOpen className="w-4.5 h-4.5" />
                </div>
                <div>
                  <h5 className="text-[10px] text-text-muted uppercase font-bold tracking-wider">Repositories</h5>
                  <span className="text-base font-bold font-mono text-text-primary mt-0.5 block">{repositories.length}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 border-t border-border-default pt-4">
                <div className="p-2.5 rounded-xl bg-success/15 text-success">
                  <Database className="w-4.5 h-4.5" />
                </div>
                <div>
                  <h5 className="text-[10px] text-text-muted uppercase font-bold tracking-wider">Indexed Codebases</h5>
                  <span className="text-base font-bold font-mono text-success mt-0.5 block">{totalIndexed}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Upload widget */}
          <div className="saas-card p-6 text-left bg-bg-card border border-border-default rounded-2xl">
            <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider block mb-4">
              Upload ZIP Repository
            </span>
            <UploadZone onUploadSuccess={fetchRepositories} />
          </div>
        </div>

        {/* Right column content (col-span-8): Welcome & Repository Grid */}
        <div className="col-span-12 lg:col-span-8 space-y-6 flex flex-col">
          
          {/* Welcome Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 select-none">
            <div className="text-left">
              <h1 className="text-2xl font-bold tracking-tight text-text-primary leading-tight">
                Repositories
              </h1>
              <p className="text-xs text-text-secondary mt-1">
                Manage codebase extraction, AST parsing, chunking rules, and vector indexing.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Mobile Search input */}
              <div className="flex md:hidden relative max-w-xs select-text">
                <Search className="absolute left-3 top-2.5 w-3.5 h-3.5 text-text-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter..."
                  className="w-full pl-9 pr-3 py-2 bg-bg-secondary border border-border-default rounded-xl text-xs placeholder:text-text-muted focus:outline-none focus:border-accent"
                />
              </div>

              <button
                onClick={fetchRepositories}
                disabled={loadingRepos}
                className="h-11 px-4 border border-border-default hover:bg-bg-hover hover:border-accent text-xs font-semibold rounded-xl transition-all cursor-pointer flex items-center gap-2"
                title="Reload Workspaces List"
              >
                <RefreshCw className={`w-4 h-4 ${loadingRepos ? "animate-spin" : ""}`} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* Main Grid View */}
          <div className="flex-1 flex flex-col">
            {loadingRepos ? (
              /* Loading Skeletons */
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="saas-card p-6 h-[300px] flex flex-col justify-between border border-border-default bg-bg-card animate-pulse"
                  >
                    <div className="space-y-4">
                      <div className="flex justify-between items-start">
                        <div className="h-6 bg-bg-hover rounded-md w-2/3" />
                        <div className="h-4 bg-bg-hover rounded-md w-1/4" />
                      </div>
                      <div className="h-10 bg-bg-hover rounded-lg w-full" />
                      <div className="space-y-2">
                        <div className="h-2.5 bg-bg-hover rounded w-full" />
                        <div className="h-2.5 bg-bg-hover rounded w-4/5" />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <div className="h-11 bg-bg-hover rounded-xl w-1/4" />
                      <div className="h-11 bg-bg-hover rounded-xl w-3/4" />
                    </div>
                  </div>
                ))}
              </div>
            ) : filteredRepos.length === 0 ? (
              /* Empty State */
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="saas-card py-24 px-6 text-center flex flex-col justify-center items-center flex-1 min-h-[350px] bg-bg-card border border-border-default rounded-2xl"
              >
                <div className="p-4 rounded-full bg-accent/5 text-accent mb-4 border border-accent/10">
                  <Compass className="w-10 h-10 animate-pulse" />
                </div>
                <h3 className="text-base font-bold text-text-primary mb-1">No repositories indexed</h3>
                <p className="text-xs text-text-secondary max-w-xs leading-relaxed">
                  {searchQuery
                    ? `No search results match "${searchQuery}". Clear your query to list all uploads.`
                    : "To get started, drag and drop a ZIP archive of your codebase into the upload area on the left."}
                </p>
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="mt-4 px-4 py-2 bg-bg-hover border border-border-default hover:border-accent text-xs font-semibold rounded-xl transition-all cursor-pointer"
                  >
                    Clear Filter
                  </button>
                )}
              </motion.div>
            ) : (
              /* Repositories Cards Grid (Gap 24px) */
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <AnimatePresence mode="popLayout">
                  {filteredRepos.map((repo) => (
                    <RepositoryCard
                      key={repo.id}
                      repo={repo}
                      onActionSuccess={fetchRepositories}
                    />
                  ))}
                </AnimatePresence>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
