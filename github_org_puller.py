#!/usr/bin/env python3
"""
GitHub Organization Repository Puller
Fetches all repositories from a GitHub organization and clones them locally.
"""

import os
import sys
import requests
import subprocess
import argparse
from typing import List, Dict, Any
import time


class GitHubOrgPuller:
    def __init__(self, token: str = None):
        """Initialize the GitHub API client.
        
        Args:
            token: GitHub personal access token (optional but recommended)
        """
        self.session = requests.Session()
        if token:
            self.session.headers.update({
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            })
        else:
            print("Warning: No GitHub token provided. API rate limits will be lower.")
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def check_ssh_agent(self) -> bool:
        """Check if SSH agent is running and has keys loaded."""
        try:
            result = subprocess.run(['ssh-add', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ SSH agent is running with loaded keys")
                return True
            else:
                print("⚠️  SSH agent is running but no keys are loaded")
                print("   Run: ssh-add ~/.ssh/id_ed25519")
                return False
        except FileNotFoundError:
            print("⚠️  SSH agent not found")
            return False
        except Exception:
            print("⚠️  Could not check SSH agent status")
            return False
    
    def get_all_repos(self, org_name: str) -> List[Dict[str, Any]]:
        """Fetch all repositories from a GitHub organization.
        
        Args:
            org_name: Name of the GitHub organization
            
        Returns:
            List of repository dictionaries
        """
        repos = []
        page = 1
        per_page = 100  # Maximum allowed by GitHub API
        
        print(f"Fetching repositories for organization: {org_name}")
        
        while True:
            url = f"https://api.github.com/orgs/{org_name}/repos"
            params = {
                'page': page,
                'per_page': per_page,
                'type': 'all',  # Include all repository types
                'sort': 'updated',
                'direction': 'desc'
            }
            
            print(f"Fetching page {page}...")
            response = self.session.get(url, params=params)
            
            if response.status_code == 404:
                raise ValueError(f"Organization '{org_name}' not found or not accessible")
            elif response.status_code == 403:
                raise ValueError("API rate limit exceeded or insufficient permissions")
            elif response.status_code != 200:
                raise ValueError(f"GitHub API error: {response.status_code} - {response.text}")
            
            page_repos = response.json()
            
            if not page_repos:  # No more repositories
                break
                
            repos.extend(page_repos)
            print(f"Found {len(page_repos)} repositories on page {page}")
            
            # Check if we've reached the last page
            if len(page_repos) < per_page:
                break
                
            page += 1
            
            # Be nice to the API - add a small delay
            time.sleep(0.1)
        
        print(f"Total repositories found: {len(repos)}")
        return repos
    
    def clone_repo(self, repo: Dict[str, Any], target_dir: str, use_ssh: bool = False) -> bool:
        """Clone a single repository.
        
        Args:
            repo: Repository dictionary from GitHub API
            target_dir: Directory to clone into
            use_ssh: Whether to use SSH URLs instead of HTTPS
            
        Returns:
            True if successful, False otherwise
        """
        repo_name = repo['name']
        clone_url = repo['ssh_url'] if use_ssh else repo['clone_url']
        repo_path = os.path.join(target_dir, repo_name)
        
        # Skip if directory already exists
        if os.path.exists(repo_path):
            print(f"⚠️  {repo_name} already exists, skipping...")
            return True
        
        print(f"📦 Cloning {repo_name}...")
        
        try:
            # Set up environment for SSH agent
            env = os.environ.copy()
            
            # For SSH, ensure we use the ssh-agent
            if use_ssh:
                # Disable SSH host key checking for automated cloning
                env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=no -o BatchMode=yes'
            
            # Clone the repository
            result = subprocess.run([
                'git', 'clone', clone_url, repo_path
            ], capture_output=True, text=True, timeout=300, env=env)  # 5 minute timeout
            
            if result.returncode == 0:
                print(f"✅ Successfully cloned {repo_name}")
                return True
            else:
                error_msg = result.stderr.strip()
                if "Permission denied" in error_msg and use_ssh:
                    print(f"❌ SSH authentication failed for {repo_name}. Make sure ssh-agent is running and key is added.")
                    print("   Try: ssh-add ~/.ssh/id_ed25519")
                else:
                    print(f"❌ Failed to clone {repo_name}: {error_msg}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout while cloning {repo_name}")
            return False
        except FileNotFoundError:
            print("❌ Git is not installed or not in PATH")
            return False
        except Exception as e:
            print(f"❌ Error cloning {repo_name}: {str(e)}")
            return False
    
    def pull_all_repos(self, org_name: str, target_dir: str = None, use_ssh: bool = False, 
                      include_forks: bool = True, include_archived: bool = True) -> None:
        """Pull all repositories from an organization.
        
        Args:
            org_name: Name of the GitHub organization
            target_dir: Directory to clone repositories into (default: org_name)
            use_ssh: Whether to use SSH URLs instead of HTTPS
            include_forks: Whether to include forked repositories
            include_archived: Whether to include archived repositories
        """
        if target_dir is None:
            target_dir = org_name
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        print(f"Cloning repositories to: {os.path.abspath(target_dir)}")
        
        # Check SSH agent if using SSH
        if use_ssh:
            print("\nChecking SSH configuration...")
            if not self.check_ssh_agent():
                print("Warning: SSH issues detected. Consider using HTTPS instead or fix SSH setup.")
                response = input("Continue anyway? (y/n): ").strip().lower()
                if response != 'y':
                    return
        
        try:
            # Get all repositories
            repos = self.get_all_repos(org_name)
            
            # Filter repositories based on options
            filtered_repos = []
            for repo in repos:
                if not include_forks and repo['fork']:
                    print(f"Skipping fork: {repo['name']}")
                    continue
                if not include_archived and repo['archived']:
                    print(f"Skipping archived repo: {repo['name']}")
                    continue
                filtered_repos.append(repo)
            
            print(f"\nWill clone {len(filtered_repos)} repositories")
            
            # Clone each repository
            successful = 0
            failed = 0
            
            for i, repo in enumerate(filtered_repos, 1):
                print(f"\n[{i}/{len(filtered_repos)}] ", end="")
                if self.clone_repo(repo, target_dir, use_ssh):
                    successful += 1
                else:
                    failed += 1
            
            # Summary
            print(f"\n{'='*50}")
            print(f"SUMMARY")
            print(f"{'='*50}")
            print(f"Total repositories: {len(filtered_repos)}")
            print(f"Successfully cloned: {successful}")
            print(f"Failed: {failed}")
            
            if failed > 0:
                print(f"\n⚠️  {failed} repositories failed to clone. Check the output above for details.")
            else:
                print(f"\n🎉 All repositories cloned successfully!")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Clone all repositories from a GitHub organization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python github_org_puller.py microsoft
  python github_org_puller.py facebook --token your_github_token
  python github_org_puller.py google --target-dir ./google-repos --ssh
  python github_org_puller.py netflix --no-forks --no-archived
        """
    )
    
    parser.add_argument('organization', help='GitHub organization name')
    parser.add_argument('--token', help='GitHub personal access token (recommended)')
    parser.add_argument('--target-dir', help='Directory to clone repositories into (default: organization name)')
    parser.add_argument('--ssh', action='store_true', help='Use SSH URLs instead of HTTPS')
    parser.add_argument('--no-forks', action='store_true', help='Exclude forked repositories')
    parser.add_argument('--no-archived', action='store_true', help='Exclude archived repositories')
    
    args = parser.parse_args()
    
    # Get token from environment variable if not provided
    token = args.token or os.getenv('GITHUB_TOKEN')
    
    # Initialize the puller
    puller = GitHubOrgPuller(token)
    
    # Pull all repositories
    puller.pull_all_repos(
        org_name=args.organization,
        target_dir=args.target_dir,
        use_ssh=args.ssh,
        include_forks=not args.no_forks,
        include_archived=not args.no_archived
    )


if __name__ == "__main__":
    main()