# GitHub Organization Cloner

A comprehensive tool for automatically cloning all repositories from a GitHub organization. This tool consists of a bash script wrapper (`auto_clone.sh`) and a Python implementation (`github_org_puller.py`) that handles SSH agent setup and repository cloning with advanced filtering options.

## Features

- **Automated SSH Setup**: Automatically starts and configures SSH agent
- **Bulk Repository Cloning**: Clone all repositories from any GitHub organization
- **Flexible Authentication**: Support for both SSH keys and GitHub tokens
- **Smart Filtering**: Options to exclude forks, archived repositories, or both
- **Progress Tracking**: Real-time progress updates with colored output
- **Error Handling**: Comprehensive error handling and recovery options
- **Rate Limit Aware**: Respects GitHub API rate limits with automatic pagination
- **Resume Capability**: Skips already cloned repositories on subsequent runs

## Prerequisites

### Required Software
- **Git**: Must be installed and accessible from command line
- **Python 3.6+**: Required for the Python script
- **Bash**: For running the wrapper script (Linux/macOS/WSL)

### Required Python Packages
```bash
pip install -r requirements.txt
```

### GitHub Access Requirements
- **SSH Key**: Set up and added to your GitHub account (recommended)
- **GitHub Token**: Personal access token (optional but recommended for higher API limits)

## Setup Instructions

### 1. Download the Scripts

Save both files to the same directory:
- `auto_clone.sh` - Bash wrapper script
- `github_org_puller.py` - Python implementation

Make the bash script executable:
```bash
chmod +x auto_clone.sh
```

### 2. Choose Your Working Directory

**Important**: Navigate to the directory where you want the organization folder to be created before running the scripts. The tools will create a directory named after the organization in your current working directory.

```bash
# Example: If you want to clone to ~/projects/microsoft/
cd ~/projects/

# Then run the script - this will create ~/projects/microsoft/ with all repos
./auto_clone.sh microsoft
```

### 3. SSH Key Setup (Recommended)

#### Generate SSH Key (if you don't have one)
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

#### Add SSH Key to GitHub
1. Copy your public key:
   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```
2. Go to GitHub Settings → SSH and GPG keys → New SSH key
3. Paste your public key and save

#### Test SSH Connection
```bash
ssh -T git@github.com
```

### 4. GitHub Token Setup (Optional but Recommended)

#### Create Personal Access Token
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (for private repos) or `public_repo` (for public repos only)
4. Copy the generated token

#### Set Environment Variable
```bash
export GITHUB_TOKEN="your_token_here"
```

Or add to your shell profile (`.bashrc`, `.zshrc`, etc.):
```bash
echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.bashrc
```

## Usage

### Basic Usage with Bash Wrapper (Recommended)

**Important**: Run these commands from the directory where you want the organization folder created.

```bash
# Navigate to your desired parent directory first
cd ~/projects/

# Clone all repositories from an organization
# This creates ~/projects/microsoft/ with all repos inside
./auto_clone.sh microsoft

# With explicit token
./auto_clone.sh microsoft ghp_your_token_here

# With custom SSH key path
./auto_clone.sh microsoft ghp_your_token_here ~/.ssh/custom_key
```

### Direct Python Usage

**Important**: Run these commands from the directory where you want the organization folder created (unless using `--target-dir`).

```bash
# Basic usage - creates ./microsoft/ in current directory
python3 github_org_puller.py microsoft

# With GitHub token
python3 github_org_puller.py facebook --token your_github_token

# Using SSH instead of HTTPS
python3 github_org_puller.py google --ssh

# Custom target directory (can be run from anywhere)
python3 github_org_puller.py netflix --target-dir ./my-netflix-repos

# Exclude forks and archived repositories
python3 github_org_puller.py kubernetes --no-forks --no-archived
```

## Command Line Options

### Bash Wrapper (`auto_clone.sh`)
```
Usage: ./auto_clone.sh <organization_name> [github_token] [ssh_key_path]

Arguments:
  organization_name    Required. Name of the GitHub organization
  github_token        Optional. GitHub personal access token
  ssh_key_path        Optional. Path to SSH private key (default: ~/.ssh/id_ed25519)

Note: The bash wrapper currently does not support custom target directories.
Use the Python script directly for this feature:
  python3 github_org_puller.py <org> --target-dir ./custom-dir
```

### Python Script (`github_org_puller.py`)
```
Usage: python3 github_org_puller.py <organization> [options]

Arguments:
  organization        Required. GitHub organization name

Options:
  --token TOKEN       GitHub personal access token
  --target-dir DIR    Directory to clone repositories into (default: organization name)
  --ssh              Use SSH URLs instead of HTTPS
  --no-forks         Exclude forked repositories
  --no-archived      Exclude archived repositories
  -h, --help         Show help message
```

## Examples

### Clone Microsoft's Public Repositories
```bash
# Navigate to where you want the microsoft/ folder created
cd ~/development/

# Using the wrapper script - creates ~/development/microsoft/
./auto_clone.sh microsoft

# Or directly with Python - creates ~/development/microsoft/
python3 github_org_puller.py microsoft
```

### Clone with Authentication for Private Repos
```bash
# Using environment variable
export GITHUB_TOKEN="ghp_your_token_here"
./auto_clone.sh your-private-org

# Or pass token directly
./auto_clone.sh your-private-org ghp_your_token_here
```

### Clone Only Active, Non-Fork Repositories
```bash
python3 github_org_puller.py kubernetes --no-forks --no-archived --ssh
```

### Clone to Custom Directory
```bash
# Use Python script directly for custom target directory
python3 github_org_puller.py docker --target-dir ./docker-projects

# The bash wrapper does not support custom target directories
# ./auto_clone.sh docker  # This will clone to ./docker/ directory
```

### Clone Large Organization with SSH
```bash
./auto_clone.sh apache
```

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GITHUB_TOKEN` | Personal access token | `ghp_xxxxxxxxxxxx` |
| `SSH_AGENT_PID` | SSH agent process ID | Auto-detected |

### SSH Key Locations

The script will automatically look for SSH keys in these locations:
- `~/.ssh/id_ed25519` (default)
- Custom path via command line argument
- Any key loaded in SSH agent

## Output and Logging

### Success Indicators
- ✅ SSH agent running with loaded keys
- ✅ Successfully cloned repository_name
- 🎉 All repositories cloned successfully!

### Warning Indicators
- ⚠️ SSH agent running but no keys loaded
- ⚠️ repository_name already exists, skipping...

### Error Indicators
- ❌ SSH authentication failed
- ❌ Failed to clone repository_name
- ❌ Git is not installed or not in PATH

### Progress Information
```
Fetching repositories for organization: microsoft
Fetching page 1...
Found 100 repositories on page 1
...
Total repositories found: 247

Will clone 247 repositories

[1/247] 📦 Cloning vscode...
✅ Successfully cloned vscode
[2/247] 📦 Cloning typescript...
✅ Successfully cloned typescript
...
```

## Troubleshooting

### SSH Issues

**Problem**: SSH authentication failed
```bash
# Solution: Check SSH agent and keys
ssh-add -l
ssh-add ~/.ssh/id_ed25519
ssh -T git@github.com
```

**Problem**: SSH key not found
```bash
# Solution: Generate new SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
# Then add to GitHub
```

### API Rate Limiting

**Problem**: API rate limit exceeded
```bash
# Solution: Use GitHub token
export GITHUB_TOKEN="your_token_here"
```

**Problem**: Organization not found
- Verify organization name spelling
- Check if organization is private (requires token)
- Ensure your token has appropriate permissions

### Permission Issues

**Problem**: Permission denied during clone
- For SSH: Ensure SSH key is added to GitHub account
- For HTTPS: Check if token has repo access permissions
- For private repos: Ensure you're a member of the organization

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `git: command not found` | Git not installed | Install Git |
| `Organization not found` | Wrong name or private org | Check name, use token |
| `Permission denied (publickey)` | SSH key issues | Set up SSH keys properly |
| `API rate limit exceeded` | Too many requests | Use GitHub token |
| `Repository already exists` | Previous run | Normal, will skip existing |

### Current Limitations

- **Working directory behavior**: Both scripts create the organization directory in your current working directory. Always `cd` to your desired parent directory first, unless using `--target-dir` with the Python script.
- **Bash wrapper target directory**: The bash wrapper doesn't support custom target directories. Use the Python script directly for this feature.
- **Parallel cloning**: Currently clones repositories sequentially. Could be enhanced for parallel processing.

## Performance Considerations

### For Large Organizations (100+ repos)
- Use SSH for faster cloning
- Set up SSH agent to avoid repeated password prompts
- Use GitHub token to avoid rate limiting
- Consider using `--no-forks` to reduce clone count
- Run during off-peak hours for better performance

### Disk Space Requirements
- Calculate approximately: `number_of_repos × average_repo_size`
- Check available disk space before running
- Consider using `--no-archived` to exclude old repositories

## Security Best Practices

1. **Never commit tokens to version control**
2. **Use environment variables for tokens**
3. **Regularly rotate GitHub tokens**
4. **Use SSH keys with passphrases**
5. **Review repository contents before cloning unknown organizations**

## Advanced Usage

### Enhancing the Bash Wrapper

If you want to add target directory support to the bash wrapper, modify `auto_clone.sh`:

```bash
# Add after line: SSH_KEY="${3:-$HOME/.ssh/id_ed25519}"
TARGET_DIR="$4"

# Modify the Python command building section:
PYTHON_CMD="python3 github_org_puller.py $ORG_NAME --ssh"

if [ -n "$GITHUB_TOKEN" ]; then
    PYTHON_CMD="$PYTHON_CMD --token $GITHUB_TOKEN"
fi

if [ -n "$TARGET_DIR" ]; then
    PYTHON_CMD="$PYTHON_CMD --target-dir $TARGET_DIR"
fi
```

### Scripting Integration
```bash
#!/bin/bash
# Clone multiple organizations
for org in microsoft google facebook; do
    echo "Cloning $org..."
    ./auto_clone.sh "$org"
done
```

### Cron Job Setup
```bash
# Add to crontab for weekly updates
0 2 * * 0 /path/to/auto_clone.sh my-org-name
```

### Custom Filtering
```python
# Modify github_org_puller.py to add custom filters
# Example: Only clone repositories with specific topics
```

## Contributing

Feel free to submit issues and enhancement requests! When contributing:

1. Test with multiple organizations
2. Ensure backward compatibility
3. Add appropriate error handling
4. Update documentation

## License

This tool is provided as-is for educational and professional use. Please respect GitHub's Terms of Service and API rate limits when using this tool.

---

**Note**: Always ensure you have permission to clone repositories, especially for private organizations. Respect repository licenses and organizational policies.