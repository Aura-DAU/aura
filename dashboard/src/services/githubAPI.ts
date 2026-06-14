import axios from 'axios';

const GITHUB_API_BASE = 'https://api.github.com';
const REPO_OWNER = 'ossdaiict';
const REPO_NAME = 'DAU-pwa';

// Initialize axios with GitHub token from environment
const api = axios.create({
  baseURL: GITHUB_API_BASE,
  headers: {
    Authorization: `token ${import.meta.env.VITE_GITHUB_TOKEN}`,
    'Accept': 'application/vnd.github.v3+json'
  }
});

export interface PullRequest {
  id: number;
  number: number;
  title: string;
  state: 'open' | 'closed';
  created_at: string;
  updated_at: string;
  merged_at?: string;
  user: { login: string; avatar_url: string };
  labels: Array<{ name: string; color: string }>;
  comments: number;
}

export interface Issue {
  id: number;
  number: number;
  title: string;
  state: 'open' | 'closed';
  created_at: string;
  updated_at: string;
  user: { login: string; avatar_url: string };
  labels: Array<{ name: string; color: string }>;
  comments: number;
}

export interface Contributor {
  login: string;
  avatar_url: string;
  contributions: number;
  profile_url: string;
}

export interface RepositoryStats {
  open_issues: number;
  open_pull_requests: number;
  total_stars: number;
  language: string;
  last_updated: string;
}

// Fetch all pull requests
export const fetchPullRequests = async (): Promise<PullRequest[]> => {
  try {
    const response = await api.get(
      `/repos/${REPO_OWNER}/${REPO_NAME}/pulls`,
      { params: { state: 'all', per_page: 100 } }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching pull requests:', error);
    throw error;
  }
};

// Fetch all issues
export const fetchIssues = async (): Promise<Issue[]> => {
  try {
    const response = await api.get(
      `/repos/${REPO_OWNER}/${REPO_NAME}/issues`,
      { params: { state: 'all', per_page: 100 } }
    );
    return response.data.filter((issue: any) => !issue.pull_request);
  } catch (error) {
    console.error('Error fetching issues:', error);
    throw error;
  }
};

// Fetch repository statistics
export const fetchRepositoryStats = async (): Promise<RepositoryStats> => {
  try {
    const response = await api.get(`/repos/${REPO_OWNER}/${REPO_NAME}`);
    return {
      open_issues: response.data.open_issues_count,
      open_pull_requests: 0,
      total_stars: response.data.stargazers_count,
      language: response.data.language,
      last_updated: response.data.updated_at
    };
  } catch (error) {
    console.error('Error fetching repository stats:', error);
    throw error;
  }
};

// Fetch contributors
export const fetchContributors = async (): Promise<Contributor[]> => {
  try {
    const response = await api.get(
      `/repos/${REPO_OWNER}/${REPO_NAME}/contributors`,
      { params: { per_page: 50 } }
    );
    return response.data.map((contributor: any) => ({
      login: contributor.login,
      avatar_url: contributor.avatar_url,
      contributions: contributor.contributions,
      profile_url: contributor.html_url
    }));
  } catch (error) {
    console.error('Error fetching contributors:', error);
    throw error;
  }
};

// Fetch commits for a specific branch
export const fetchCommits = async (branch: string = 'main') => {
  try {
    const response = await api.get(
      `/repos/${REPO_OWNER}/${REPO_NAME}/commits`,
      { params: { sha: branch, per_page: 50 } }
    );
    return response.data;
  } catch (error) {
    console.error('Error fetching commits:', error);
    throw error;
  }
};
