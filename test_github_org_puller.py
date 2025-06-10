import os
import sys
import types
import pytest
import tempfile
import shutil
from unittest import mock
from github_org_puller import GitHubOrgPuller

class DummyResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json = json_data or []
        self.text = text
    def json(self):
        return self._json

def test_check_ssh_agent_success(monkeypatch):
    puller = GitHubOrgPuller()
    monkeypatch.setattr('subprocess.run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='key', stderr=''))
    assert puller.check_ssh_agent() is True

def test_check_ssh_agent_no_keys(monkeypatch):
    puller = GitHubOrgPuller()
    monkeypatch.setattr('subprocess.run', lambda *a, **k: types.SimpleNamespace(returncode=1, stdout='', stderr=''))
    assert puller.check_ssh_agent() is False

def test_get_all_repos_success(monkeypatch):
    puller = GitHubOrgPuller()
    # Simulate two pages
    responses = [
        DummyResponse(200, [{"name": "repo1", "fork": False, "archived": False}, {"name": "repo2", "fork": False, "archived": False}]),
        DummyResponse(200, [])
    ]
    def fake_get(url, params=None):
        return responses.pop(0)
    puller.session.get = fake_get
    repos = puller.get_all_repos("dummyorg")
    assert len(repos) == 2
    assert repos[0]["name"] == "repo1"

def test_get_all_repos_404(monkeypatch):
    puller = GitHubOrgPuller()
    puller.session.get = lambda url, params=None: DummyResponse(404)
    with pytest.raises(ValueError):
        puller.get_all_repos("notfound")

def test_clone_repo_success(monkeypatch):
    puller = GitHubOrgPuller()
    repo = {"name": "repo1", "clone_url": "https://github.com/org/repo1.git", "ssh_url": "git@github.com:org/repo1.git"}
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr('os.path.exists', lambda path: False)
        monkeypatch.setattr('subprocess.run', lambda *a, **k: types.SimpleNamespace(returncode=0, stdout='', stderr=''))
        assert puller.clone_repo(repo, tmpdir, use_ssh=False) is True

def test_clone_repo_already_exists(monkeypatch):
    puller = GitHubOrgPuller()
    repo = {"name": "repo1", "clone_url": "https://github.com/org/repo1.git", "ssh_url": "git@github.com:org/repo1.git"}
    monkeypatch.setattr('os.path.exists', lambda path: True)
    assert puller.clone_repo(repo, "/tmp", use_ssh=False) is True

def test_clone_repo_fail(monkeypatch):
    puller = GitHubOrgPuller()
    repo = {"name": "repo1", "clone_url": "https://github.com/org/repo1.git", "ssh_url": "git@github.com:org/repo1.git"}
    monkeypatch.setattr('os.path.exists', lambda path: False)
    monkeypatch.setattr('subprocess.run', lambda *a, **k: types.SimpleNamespace(returncode=1, stdout='', stderr='Permission denied'))
    assert puller.clone_repo(repo, "/tmp", use_ssh=True) is False

def test_pull_all_repos_filters(monkeypatch):
    puller = GitHubOrgPuller()
    # Simulate get_all_repos returns 3 repos
    monkeypatch.setattr(puller, 'get_all_repos', lambda org: [
        {"name": "repo1", "fork": False, "archived": False, "clone_url": "", "ssh_url": ""},
        {"name": "repo2", "fork": True, "archived": False, "clone_url": "", "ssh_url": ""},
        {"name": "repo3", "fork": False, "archived": True, "clone_url": "", "ssh_url": ""},
    ])
    monkeypatch.setattr(puller, 'clone_repo', lambda repo, target_dir, use_ssh: True)
    # Should only clone repo1 if both filters are off
    puller.pull_all_repos("dummyorg", target_dir=None, use_ssh=False, include_forks=False, include_archived=False)
