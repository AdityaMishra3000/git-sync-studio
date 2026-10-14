
export type Repository = {
  id: string;
  owner: string;
  name: string;
  github_repo_id: number;
  default_branch: string;
  visibility: string;
  sync_status: string;
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
};

export type User = {
  id: string;
  email: string;
  name: string | null;
};
