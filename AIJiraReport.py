"""
JIRA AI Agent using Ollama and Autogen with Advanced Reporting Features
Requires: pip install pyautogen jira requests atlassian-python-api pandas matplotlib
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import autogen
from jira import JIRA
from jira.exceptions import JIRAError
from atlassian import Confluence
from atlassian.errors import ApiError

# Configuration
config_list = [
    {
        "model": "qwen2.5",  # or any model you have in Ollama
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",  # Ollama doesn't need a real key
    }
]

# JIRA Configuration
JIRA_CONFIG = {
    "server": "https://vikasrathod87.atlassian.net/",
    "email": "vikas.rathod87@gmail.com",
    "api_token": "JIRA_API_TOKEN_HERE"
}

# Confluence Configuration (uses same credentials as JIRA)
CONFLUENCE_CONFIG = {
    "url": "https://vikasrathod87.atlassian.net/wiki",
    "username": "vikas.rathod87@gmail.com",
    "password": "JIRA_API_TOKEN_HERE"
}


class JIRAReports:
    """JIRA Reporting functionality"""

    def __init__(self, jira: JIRA):
        self.jira = jira

    def generate_sprint_report(self, board_id: int, sprint_id: int = None) -> Dict:
        """Generate a comprehensive sprint report

        Args:
            board_id: The board ID
            sprint_id: Optional sprint ID. If None, uses active sprint
        """
        try:
            # Get sprint info
            if sprint_id:
                sprint = self.jira.sprint(sprint_id)
            else:
                # Get active sprint
                sprints = self.jira.sprints(board_id, state='active')
                if not sprints:
                    return {"success": False, "error": "No active sprint found"}
                sprint = sprints[0]

            # Get sprint issues
            issues = self.jira.search_issues(
                f'sprint = {sprint.id}',
                maxResults=500,
                fields='summary,status,assignee,priority,issuetype,created,resolutiondate,timeoriginalestimate,timespent'
            )

            # Analyze issues
            total_issues = len(issues)
            completed_issues = 0
            in_progress_issues = 0
            todo_issues = 0
            by_assignee = {}
            by_type = {}
            by_priority = {}
            total_estimate = 0
            total_spent = 0

            for issue in issues:
                status = issue.fields.status.name.lower()

                if status in ['done', 'closed', 'resolved']:
                    completed_issues += 1
                elif status in ['in progress', 'in review']:
                    in_progress_issues += 1
                else:
                    todo_issues += 1

                # By assignee
                assignee = str(issue.fields.assignee) if issue.fields.assignee else "Unassigned"
                by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

                # By type
                issue_type = issue.fields.issuetype.name
                by_type[issue_type] = by_type.get(issue_type, 0) + 1

                # By priority
                if issue.fields.priority:
                    priority = issue.fields.priority.name
                    by_priority[priority] = by_priority.get(priority, 0) + 1

                # Time tracking
                if issue.fields.timeoriginalestimate:
                    total_estimate += issue.fields.timeoriginalestimate
                if issue.fields.timespent:
                    total_spent += issue.fields.timespent

            completion_rate = (completed_issues / total_issues * 100) if total_issues > 0 else 0

            return {
                "success": True,
                "sprint_name": sprint.name,
                "sprint_id": sprint.id,
                "sprint_state": sprint.state,
                "start_date": str(sprint.startDate) if hasattr(sprint, 'startDate') else None,
                "end_date": str(sprint.endDate) if hasattr(sprint, 'endDate') else None,
                "summary": {
                    "total_issues": total_issues,
                    "completed": completed_issues,
                    "in_progress": in_progress_issues,
                    "todo": todo_issues,
                    "completion_rate": round(completion_rate, 2)
                },
                "by_assignee": by_assignee,
                "by_type": by_type,
                "by_priority": by_priority,
                "time_tracking": {
                    "total_estimate_hours": round(total_estimate / 3600, 2) if total_estimate else 0,
                    "total_spent_hours": round(total_spent / 3600, 2) if total_spent else 0
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_project_summary(self, project_key: str) -> Dict:
        """Generate overall project summary report

        Args:
            project_key: The project key
        """
        try:
            # Get all issues in project
            issues = self.jira.search_issues(
                f'project = {project_key}',
                maxResults=1000,
                fields='summary,status,assignee,priority,issuetype,created,resolutiondate,labels'
            )

            total_issues = len(issues)
            by_status = {}
            by_assignee = {}
            by_type = {}
            by_priority = {}
            labels_count = {}

            open_issues = 0
            closed_issues = 0

            for issue in issues:
                # Status
                status = issue.fields.status.name
                by_status[status] = by_status.get(status, 0) + 1

                if status.lower() in ['done', 'closed', 'resolved']:
                    closed_issues += 1
                else:
                    open_issues += 1

                # Assignee
                assignee = str(issue.fields.assignee) if issue.fields.assignee else "Unassigned"
                by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

                # Type
                issue_type = issue.fields.issuetype.name
                by_type[issue_type] = by_type.get(issue_type, 0) + 1

                # Priority
                if issue.fields.priority:
                    priority = issue.fields.priority.name
                    by_priority[priority] = by_priority.get(priority, 0) + 1

                # Labels
                if issue.fields.labels:
                    for label in issue.fields.labels:
                        labels_count[label] = labels_count.get(label, 0) + 1

            return {
                "success": True,
                "project_key": project_key,
                "summary": {
                    "total_issues": total_issues,
                    "open_issues": open_issues,
                    "closed_issues": closed_issues
                },
                "by_status": by_status,
                "by_assignee": by_assignee,
                "by_type": by_type,
                "by_priority": by_priority,
                "top_labels": dict(sorted(labels_count.items(), key=lambda x: x[1], reverse=True)[:10])
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_user_workload_report(self, project_key: str = None) -> Dict:
        """Generate workload report by user

        Args:
            project_key: Optional project key to filter by
        """
        try:
            jql = f'project = {project_key} AND status not in (Done, Closed, Resolved)' if project_key else 'status not in (Done, Closed, Resolved)'

            issues = self.jira.search_issues(
                jql,
                maxResults=1000,
                fields='assignee,summary,status,priority,issuetype'
            )

            workload = {}

            for issue in issues:
                assignee = str(issue.fields.assignee) if issue.fields.assignee else "Unassigned"

                if assignee not in workload:
                    workload[assignee] = {
                        "total": 0,
                        "by_status": {},
                        "by_priority": {},
                        "issues": []
                    }

                workload[assignee]["total"] += 1

                # By status
                status = issue.fields.status.name
                workload[assignee]["by_status"][status] = workload[assignee]["by_status"].get(status, 0) + 1

                # By priority
                if issue.fields.priority:
                    priority = issue.fields.priority.name
                    workload[assignee]["by_priority"][priority] = workload[assignee]["by_priority"].get(priority, 0) + 1

                # Add issue details
                workload[assignee]["issues"].append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": status,
                    "priority": issue.fields.priority.name if issue.fields.priority else "None"
                })

            # Sort by workload
            sorted_workload = dict(sorted(workload.items(), key=lambda x: x[1]["total"], reverse=True))

            return {
                "success": True,
                "project": project_key if project_key else "All projects",
                "workload": sorted_workload
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_velocity_report(self, board_id: int, num_sprints: int = 5) -> Dict:
        """Generate velocity report for recent sprints

        Args:
            board_id: The board ID
            num_sprints: Number of recent sprints to analyze
        """
        try:
            # Get recent closed sprints
            sprints = self.jira.sprints(board_id, state='closed', maxResults=num_sprints)

            if not sprints:
                return {"success": False, "error": "No closed sprints found"}

            velocity_data = []

            for sprint in sprints:
                issues = self.jira.search_issues(
                    f'sprint = {sprint.id}',
                    maxResults=500,
                    fields='status,issuetype'
                )

                total = len(issues)
                completed = sum(
                    1 for issue in issues if issue.fields.status.name.lower() in ['done', 'closed', 'resolved'])

                velocity_data.append({
                    "sprint_name": sprint.name,
                    "sprint_id": sprint.id,
                    "total_issues": total,
                    "completed_issues": completed,
                    "completion_rate": round((completed / total * 100) if total > 0 else 0, 2)
                })

            # Calculate average velocity
            avg_completed = sum(s["completed_issues"] for s in velocity_data) / len(
                velocity_data) if velocity_data else 0
            avg_total = sum(s["total_issues"] for s in velocity_data) / len(velocity_data) if velocity_data else 0

            return {
                "success": True,
                "board_id": board_id,
                "sprints_analyzed": len(velocity_data),
                "velocity_data": velocity_data,
                "averages": {
                    "avg_completed": round(avg_completed, 2),
                    "avg_total": round(avg_total, 2),
                    "avg_completion_rate": round((avg_completed / avg_total * 100) if avg_total > 0 else 0, 2)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_issue_aging_report(self, project_key: str, days_threshold: int = 30) -> Dict:
        """Generate report of aging issues

        Args:
            project_key: The project key
            days_threshold: Number of days to consider an issue as aging
        """
        try:
            issues = self.jira.search_issues(
                f'project = {project_key} AND status not in (Done, Closed, Resolved)',
                maxResults=1000,
                fields='summary,status,created,assignee,priority'
            )

            aging_issues = []
            now = datetime.now()

            for issue in issues:
                created = datetime.strptime(issue.fields.created[:19], '%Y-%m-%dT%H:%M:%S')
                age_days = (now - created).days

                if age_days >= days_threshold:
                    aging_issues.append({
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "status": issue.fields.status.name,
                        "assignee": str(issue.fields.assignee) if issue.fields.assignee else "Unassigned",
                        "priority": issue.fields.priority.name if issue.fields.priority else "None",
                        "age_days": age_days,
                        "created": str(created.date())
                    })

            # Sort by age
            aging_issues.sort(key=lambda x: x["age_days"], reverse=True)

            return {
                "success": True,
                "project_key": project_key,
                "threshold_days": days_threshold,
                "total_aging_issues": len(aging_issues),
                "aging_issues": aging_issues
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_bug_report(self, project_key: str) -> Dict:
        """Generate comprehensive bug report

        Args:
            project_key: The project key
        """
        try:
            issues = self.jira.search_issues(
                f'project = {project_key} AND issuetype = Bug',
                maxResults=1000,
                fields='summary,status,priority,created,resolutiondate,assignee'
            )

            total_bugs = len(issues)
            open_bugs = 0
            closed_bugs = 0
            by_priority = {}
            by_status = {}
            avg_resolution_time_days = 0
            resolution_times = []

            for issue in issues:
                status = issue.fields.status.name
                by_status[status] = by_status.get(status, 0) + 1

                if status.lower() in ['done', 'closed', 'resolved']:
                    closed_bugs += 1

                    # Calculate resolution time
                    if issue.fields.resolutiondate:
                        created = datetime.strptime(issue.fields.created[:19], '%Y-%m-%dT%H:%M:%S')
                        resolved = datetime.strptime(issue.fields.resolutiondate[:19], '%Y-%m-%dT%H:%M:%S')
                        resolution_time = (resolved - created).days
                        resolution_times.append(resolution_time)
                else:
                    open_bugs += 1

                # Priority
                if issue.fields.priority:
                    priority = issue.fields.priority.name
                    by_priority[priority] = by_priority.get(priority, 0) + 1

            if resolution_times:
                avg_resolution_time_days = sum(resolution_times) / len(resolution_times)

            return {
                "success": True,
                "project_key": project_key,
                "summary": {
                    "total_bugs": total_bugs,
                    "open_bugs": open_bugs,
                    "closed_bugs": closed_bugs,
                    "avg_resolution_time_days": round(avg_resolution_time_days, 2)
                },
                "by_status": by_status,
                "by_priority": by_priority
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_custom_report(self, jql: str, report_name: str = "Custom Report") -> Dict:
        """Generate a custom report based on JQL query

        Args:
            jql: JQL query string
            report_name: Name for the report
        """
        try:
            issues = self.jira.search_issues(
                jql,
                maxResults=1000,
                fields='summary,status,assignee,priority,issuetype,created,updated'
            )

            by_status = {}
            by_assignee = {}
            by_type = {}
            by_priority = {}

            issue_list = []

            for issue in issues:
                # Status
                status = issue.fields.status.name
                by_status[status] = by_status.get(status, 0) + 1

                # Assignee
                assignee = str(issue.fields.assignee) if issue.fields.assignee else "Unassigned"
                by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

                # Type
                issue_type = issue.fields.issuetype.name
                by_type[issue_type] = by_type.get(issue_type, 0) + 1

                # Priority
                if issue.fields.priority:
                    priority = issue.fields.priority.name
                    by_priority[priority] = by_priority.get(priority, 0) + 1

                issue_list.append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": status,
                    "assignee": assignee,
                    "type": issue_type,
                    "priority": issue.fields.priority.name if issue.fields.priority else "None"
                })

            return {
                "success": True,
                "report_name": report_name,
                "jql": jql,
                "total_issues": len(issues),
                "by_status": by_status,
                "by_assignee": by_assignee,
                "by_type": by_type,
                "by_priority": by_priority,
                "issues": issue_list[:50]  # Limit to first 50 for display
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


class JIRATools:
    """JIRA API wrapper with common operations"""

    def __init__(self, server: str, email: str, api_token: str):
        self.jira = JIRA(
            server=server,
            basic_auth=(email, api_token)
        )
        self.reports = JIRAReports(self.jira)

    def create_issue(self, project_key: str, summary: str, description: str,
                     issue_type: str = "Task") -> Dict:
        """Create a new JIRA issue"""
        try:
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
            }
            new_issue = self.jira.create_issue(fields=issue_dict)
            return {
                "success": True,
                "issue_key": new_issue.key,
                "issue_id": new_issue.id,
                "url": f"{self.jira._options['server']}/browse/{new_issue.key}"
            }
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def get_issue(self, issue_key: str) -> Dict:
        """Get issue details"""
        try:
            issue = self.jira.issue(issue_key)
            return {
                "success": True,
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": str(issue.fields.assignee) if issue.fields.assignee else "Unassigned",
                "priority": issue.fields.priority.name if issue.fields.priority else "None"
            }
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def search_issues(self, jql: str, max_results: int = 50) -> Dict:
        """Search issues using JQL"""
        try:
            issues = self.jira.search_issues(jql, maxResults=max_results)
            results = []
            for issue in issues:
                results.append({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name
                })
            return {"success": True, "count": len(results), "issues": results}
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """Update an existing issue"""
        try:
            issue = self.jira.issue(issue_key)
            issue.update(fields=fields)
            return {"success": True, "message": f"Issue {issue_key} updated"}
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def add_comment(self, issue_key: str, comment: str) -> Dict:
        """Add a comment to an issue"""
        try:
            self.jira.add_comment(issue_key, comment)
            return {"success": True, "message": f"Comment added to {issue_key}"}
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def transition_issue(self, issue_key: str, transition_name: str) -> Dict:
        """Transition issue to a new status"""
        try:
            transitions = self.jira.transitions(issue_key)
            transition_id = None

            for t in transitions:
                if t['name'].lower() == transition_name.lower():
                    transition_id = t['id']
                    break

            if transition_id:
                self.jira.transition_issue(issue_key, transition_id)
                return {"success": True, "message": f"Issue {issue_key} transitioned to {transition_name}"}
            else:
                available = [t['name'] for t in transitions]
                return {"success": False, "error": f"Transition not found. Available: {available}"}
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def assign_issue(self, issue_key: str, assignee: str) -> Dict:
        """Assign an issue to a user"""
        try:
            issue = self.jira.issue(issue_key)

            if assignee in [None, '', 'unassign', 'unassigned']:
                issue.update(fields={'assignee': None})
                return {
                    "success": True,
                    "message": f"Issue {issue_key} unassigned",
                    "assignee": "Unassigned"
                }
            elif assignee.lower() in ['me', 'myself', 'self']:
                current_user_id = self.jira.current_user()
                issue.update(fields={'assignee': {'accountId': current_user_id}})
                return {
                    "success": True,
                    "message": f"Issue {issue_key} assigned to you",
                    "assignee": "You (current user)",
                    "accountId": current_user_id
                }
            else:
                try:
                    if assignee.startswith('557058:') or assignee.startswith('5'):
                        issue.update(fields={'assignee': {'accountId': assignee}})
                        return {
                            "success": True,
                            "message": f"Issue {issue_key} assigned successfully",
                            "assignee": assignee
                        }

                    assignable_users = self.jira.search_assignable_users_for_issues(
                        '',
                        issue_key=issue_key,
                        maxResults=100
                    )

                    matched_user = None
                    assignee_lower = assignee.lower()

                    for user in assignable_users:
                        if (user.displayName.lower() == assignee_lower or
                                assignee_lower in user.displayName.lower()):
                            matched_user = user
                            break

                    if matched_user:
                        issue.update(fields={'assignee': {'accountId': matched_user.accountId}})
                        return {
                            "success": True,
                            "message": f"Issue {issue_key} assigned to {matched_user.displayName}",
                            "assignee": matched_user.displayName,
                            "accountId": matched_user.accountId
                        }

                    users = self.jira.search_users(assignee, maxResults=10)

                    if users:
                        user = users[0]
                        issue.update(fields={'assignee': {'accountId': user.accountId}})
                        return {
                            "success": True,
                            "message": f"Issue {issue_key} assigned to {user.displayName}",
                            "assignee": user.displayName,
                            "accountId": user.accountId
                        }

                    return {
                        "success": False,
                        "error": f"User '{assignee}' not found. Use 'me' for self-assignment or get assignable users first."
                    }

                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to assign user: {str(e)}"
                    }

        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def get_assignable_users(self, project_key: str = None, issue_key: str = None,
                             max_results: int = 50) -> Dict:
        """Get list of users who can be assigned to issues"""
        try:
            if issue_key:
                users = self.jira.search_assignable_users_for_issues(
                    '',
                    issue_key=issue_key,
                    maxResults=max_results
                )
            elif project_key:
                users = self.jira.search_assignable_users_for_projects(
                    '',
                    project_key,
                    maxResults=max_results
                )
            else:
                return {
                    "success": False,
                    "error": "Either project_key or issue_key must be provided"
                }

            user_list = []
            for user in users:
                user_info = {
                    "accountId": user.accountId,
                    "displayName": user.displayName,
                    "active": user.active
                }
                if hasattr(user, 'emailAddress'):
                    user_info["emailAddress"] = user.emailAddress

                user_list.append(user_info)

            return {
                "success": True,
                "count": len(user_list),
                "users": user_list,
                "note": "Use displayName or accountId to assign issues."
            }
        except JIRAError as e:
            return {"success": False, "error": str(e)}

    def get_boards(self, project_key: str = None) -> Dict:
        """Get list of boards, optionally filtered by project"""
        try:
            boards = self.jira.boards(projectKeyOrID=project_key) if project_key else self.jira.boards()

            board_list = []
            for board in boards:
                board_list.append({
                    "id": board.id,
                    "name": board.name,
                    "type": board.type
                })

            return {
                "success": True,
                "count": len(board_list),
                "boards": board_list
            }
        except JIRAError as e:
            return {"success": False, "error": str(e)}


class ConfluenceTools:
    """Confluence API wrapper for page operations"""

    def __init__(self, url: str, username: str, password: str):
        self.confluence = Confluence(
            url=url,
            username=username,
            password=password,
            cloud=True
        )

    def create_page(self, space_key: str, title: str, body: str,
                    parent_id: str = None) -> Dict:
        """Create a new Confluence page"""
        try:
            page = self.confluence.create_page(
                space=space_key,
                title=title,
                body=body,
                parent_id=parent_id,
                type='page',
                representation='storage'
            )

            return {
                "success": True,
                "page_id": page['id'],
                "title": page['title'],
                "url": f"{self.confluence.url}/pages/{page['id']}",
                "web_url": page['_links']['webui']
            }
        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to create page: {str(e)}"}

    def get_page(self, page_id: str = None, title: str = None,
                 space_key: str = None) -> Dict:
        """Get a Confluence page by ID or title"""
        try:
            if page_id:
                page = self.confluence.get_page_by_id(
                    page_id=page_id,
                    expand='body.storage,version,space'
                )
            elif title and space_key:
                page = self.confluence.get_page_by_title(
                    space=space_key,
                    title=title,
                    expand='body.storage,version,space'
                )
            else:
                return {
                    "success": False,
                    "error": "Either page_id or (title + space_key) must be provided"
                }

            if page:
                return {
                    "success": True,
                    "page_id": page['id'],
                    "title": page['title'],
                    "space": page['space']['key'],
                    "version": page['version']['number'],
                    "url": page['_links']['webui'],
                    "body": page['body']['storage']['value']
                }
            else:
                return {"success": False, "error": "Page not found"}

        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to get page: {str(e)}"}

    def update_page(self, page_id: str, title: str = None, body: str = None) -> Dict:
        """Update an existing Confluence page"""
        try:
            current_page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand='body.storage,version'
            )

            if not current_page:
                return {"success": False, "error": "Page not found"}

            new_title = title if title else current_page['title']
            new_body = body if body else current_page['body']['storage']['value']

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=new_title,
                body=new_body,
                parent_id=None,
                type='page',
                representation='storage',
                minor_edit=False
            )

            return {
                "success": True,
                "page_id": updated_page['id'],
                "title": updated_page['title'],
                "version": updated_page['version']['number'],
                "url": updated_page['_links']['webui']
            }

        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to update page: {str(e)}"}

    def delete_page(self, page_id: str) -> Dict:
        """Delete a Confluence page"""
        try:
            self.confluence.remove_page(page_id)
            return {
                "success": True,
                "message": f"Page {page_id} deleted successfully"
            }
        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to delete page: {str(e)}"}

    def get_spaces(self, limit: int = 25) -> Dict:
        """Get list of Confluence spaces"""
        try:
            spaces = self.confluence.get_all_spaces(
                start=0,
                limit=limit,
                expand='description.plain'
            )

            space_list = []
            for space in spaces['results']:
                space_info = {
                    "key": space['key'],
                    "name": space['name'],
                    "type": space['type'],
                    "id": space['id']
                }
                if 'description' in space and space['description']:
                    space_info['description'] = space['description'].get('plain', {}).get('value', '')

                space_list.append(space_info)

            return {
                "success": True,
                "count": len(space_list),
                "spaces": space_list
            }
        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to get spaces: {str(e)}"}

    def search_pages(self, cql: str, limit: int = 25) -> Dict:
        """Search Confluence pages using CQL"""
        try:
            results = self.confluence.cql(cql, limit=limit)

            pages = []
            for result in results['results']:
                if result['content']['type'] == 'page':
                    page_info = {
                        "id": result['content']['id'],
                        "title": result['content']['title'],
                        "space": result['content']['space']['key'],
                        "url": result['content']['_links']['webui']
                    }
                    pages.append(page_info)

            return {
                "success": True,
                "count": len(pages),
                "pages": pages
            }
        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to search pages: {str(e)}"}

    def link_jira_issue_to_page(self, page_id: str, issue_key: str) -> Dict:
        """Add a JIRA issue macro to a Confluence page"""
        try:
            page = self.confluence.get_page_by_id(
                page_id=page_id,
                expand='body.storage,version'
            )

            if not page:
                return {"success": False, "error": "Page not found"}

            jira_macro = f'''
            <ac:structured-macro ac:name="jira" ac:schema-version="1">
                <ac:parameter ac:name="key">{issue_key}</ac:parameter>
            </ac:structured-macro>
            '''

            new_body = page['body']['storage']['value'] + jira_macro

            updated_page = self.confluence.update_page(
                page_id=page_id,
                title=page['title'],
                body=new_body,
                representation='storage'
            )

            return {
                "success": True,
                "message": f"JIRA issue {issue_key} linked to page {page_id}",
                "page_url": updated_page['_links']['webui']
            }

        except ApiError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Failed to link JIRA issue: {str(e)}"}

    def create_report_page(self, space_key: str, title: str, report_data: Dict) -> Dict:
        """Create a formatted Confluence page from a report

        Args:
            space_key: Space key
            title: Page title
            report_data: Report data dictionary
        """
        try:
            # Format report data as HTML
            html_body = self._format_report_as_html(report_data)

            page = self.confluence.create_page(
                space=space_key,
                title=title,
                body=html_body,
                type='page',
                representation='storage'
            )

            return {
                "success": True,
                "page_id": page['id'],
                "title": page['title'],
                "url": page['_links']['webui']
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _format_report_as_html(self, report_data: Dict) -> str:
        """Convert report data to HTML format"""
        html = "<h1>Report Summary</h1>"

        for key, value in report_data.items():
            if key == "success":
                continue

            html += f"<h2>{key.replace('_', ' ').title()}</h2>"

            if isinstance(value, dict):
                html += "<table><tbody>"
                for k, v in value.items():
                    html += f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"
                html += "</tbody></table>"
            elif isinstance(value, list):
                html += "<ul>"
                for item in value[:20]:  # Limit to first 20 items
                    if isinstance(item, dict):
                        html += f"<li>{json.dumps(item)}</li>"
                    else:
                        html += f"<li>{item}</li>"
                html += "</ul>"
            else:
                html += f"<p>{value}</p>"

        return html


# Initialize tools
jira_tools = JIRATools(
    server=JIRA_CONFIG["server"],
    email=JIRA_CONFIG["email"],
    api_token=JIRA_CONFIG["api_token"]
)

confluence_tools = ConfluenceTools(
    url=CONFLUENCE_CONFIG["url"],
    username=CONFLUENCE_CONFIG["username"],
    password=CONFLUENCE_CONFIG["password"]
)


# JIRA function wrappers
def create_jira_issue(project_key: str, summary: str, description: str,
                      issue_type: str = "Task") -> str:
    """Create a new JIRA issue"""
    result = jira_tools.create_issue(project_key, summary, description, issue_type)
    return json.dumps(result, indent=2)


def get_jira_issue(issue_key: str) -> str:
    """Get JIRA issue details"""
    result = jira_tools.get_issue(issue_key)
    return json.dumps(result, indent=2)


def search_jira_issues(jql: str, max_results: int = 50) -> str:
    """Search JIRA issues using JQL"""
    result = jira_tools.search_issues(jql, max_results)
    return json.dumps(result, indent=2)


def update_jira_issue(issue_key: str, summary: str = None,
                      description: str = None) -> str:
    """Update a JIRA issue"""
    fields = {}
    if summary:
        fields['summary'] = summary
    if description:
        fields['description'] = description
    result = jira_tools.update_issue(issue_key, fields)
    return json.dumps(result, indent=2)


def add_jira_comment(issue_key: str, comment: str) -> str:
    """Add a comment to a JIRA issue"""
    result = jira_tools.add_comment(issue_key, comment)
    return json.dumps(result, indent=2)


def transition_jira_issue(issue_key: str, transition_name: str) -> str:
    """Transition a JIRA issue"""
    result = jira_tools.transition_issue(issue_key, transition_name)
    return json.dumps(result, indent=2)


def assign_jira_issue(issue_key: str, assignee: str) -> str:
    """Assign a JIRA issue to a user"""
    result = jira_tools.assign_issue(issue_key, assignee)
    return json.dumps(result, indent=2)


def get_assignable_users(project_key: str = None, issue_key: str = None) -> str:
    """Get list of assignable users"""
    result = jira_tools.get_assignable_users(project_key, issue_key)
    return json.dumps(result, indent=2)


def get_jira_boards(project_key: str = None) -> str:
    """Get list of JIRA boards, optionally filtered by project

    Args:
        project_key: Optional project key to filter boards
    """
    result = jira_tools.get_boards(project_key)
    return json.dumps(result, indent=2)


# Report function wrappers
def generate_sprint_report(board_id: int, sprint_id: int = None) -> str:
    """Generate comprehensive sprint report

    Args:
        board_id: The board ID
        sprint_id: Optional sprint ID. If None, uses active sprint
    """
    result = jira_tools.reports.generate_sprint_report(board_id, sprint_id)
    return json.dumps(result, indent=2)


def generate_project_summary(project_key: str) -> str:
    """Generate overall project summary report

    Args:
        project_key: The project key (e.g., 'SCRUM')
    """
    result = jira_tools.reports.generate_project_summary(project_key)
    return json.dumps(result, indent=2)


def generate_user_workload_report(project_key: str = None) -> str:
    """Generate workload report by user

    Args:
        project_key: Optional project key to filter by
    """
    result = jira_tools.reports.generate_user_workload_report(project_key)
    return json.dumps(result, indent=2)


def generate_velocity_report(board_id: int, num_sprints: int = 5) -> str:
    """Generate velocity report for recent sprints

    Args:
        board_id: The board ID
        num_sprints: Number of recent sprints to analyze (default: 5)
    """
    result = jira_tools.reports.generate_velocity_report(board_id, num_sprints)
    return json.dumps(result, indent=2)


def generate_issue_aging_report(project_key: str, days_threshold: int = 30) -> str:
    """Generate report of aging issues

    Args:
        project_key: The project key
        days_threshold: Number of days to consider an issue as aging (default: 30)
    """
    result = jira_tools.reports.generate_issue_aging_report(project_key, days_threshold)
    return json.dumps(result, indent=2)


def generate_bug_report(project_key: str) -> str:
    """Generate comprehensive bug report

    Args:
        project_key: The project key
    """
    result = jira_tools.reports.generate_bug_report(project_key)
    return json.dumps(result, indent=2)


def generate_custom_report(jql: str, report_name: str = "Custom Report") -> str:
    """Generate a custom report based on JQL query

    Args:
        jql: JQL query string
        report_name: Name for the report
    """
    result = jira_tools.reports.generate_custom_report(jql, report_name)
    return json.dumps(result, indent=2)


# Confluence function wrappers
def create_confluence_page(space_key: str, title: str, body: str,
                           parent_id: str = None) -> str:
    """Create a new Confluence page"""
    result = confluence_tools.create_page(space_key, title, body, parent_id)
    return json.dumps(result, indent=2)


def get_confluence_page(page_id: str = None, title: str = None,
                        space_key: str = None) -> str:
    """Get a Confluence page"""
    result = confluence_tools.get_page(page_id, title, space_key)
    return json.dumps(result, indent=2)


def update_confluence_page(page_id: str, title: str = None, body: str = None) -> str:
    """Update a Confluence page"""
    result = confluence_tools.update_page(page_id, title, body)
    return json.dumps(result, indent=2)


def delete_confluence_page(page_id: str) -> str:
    """Delete a Confluence page"""
    result = confluence_tools.delete_page(page_id)
    return json.dumps(result, indent=2)


def get_confluence_spaces(limit: int = 25) -> str:
    """Get list of Confluence spaces"""
    result = confluence_tools.get_spaces(limit)
    return json.dumps(result, indent=2)


def search_confluence_pages(cql: str, limit: int = 25) -> str:
    """Search Confluence pages using CQL"""
    result = confluence_tools.search_pages(cql, limit)
    return json.dumps(result, indent=2)


def link_jira_to_confluence(page_id: str, issue_key: str) -> str:
    """Link a JIRA issue to a Confluence page"""
    result = confluence_tools.link_jira_issue_to_page(page_id, issue_key)
    return json.dumps(result, indent=2)


def create_report_in_confluence(space_key: str, title: str, report_json: str) -> str:
    """Create a Confluence page from a JIRA report

    Args:
        space_key: Confluence space key
        title: Page title
        report_json: JSON string of the report data
    """
    try:
        report_data = json.loads(report_json)
        result = confluence_tools.create_report_page(space_key, title, report_data)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


# LLM Configuration
llm_config = {
    "config_list": config_list,
    "timeout": 120,
    "temperature": 0.7,
}

# Create assistant agent
assistant = autogen.AssistantAgent(
    name="JiraAssistant",
    llm_config=llm_config,
    system_message="""You are a helpful JIRA and Confluence assistant with advanced reporting capabilities.

    JIRA Operations:
    - Create, search, update issues
    - Manage comments, transitions, assignments
    - Get boards and sprint information

    JIRA Reports (NEW):
    - Sprint Reports: Detailed sprint analysis with completion rates, assignee distribution
    - Project Summary: Overall project health and metrics
    - User Workload: Current workload distribution across team members
    - Velocity Reports: Team velocity trends over multiple sprints
    - Issue Aging: Identify stale/aging issues that need attention
    - Bug Reports: Comprehensive bug analysis and trends
    - Custom Reports: Create reports using any JQL query

    Confluence Operations:
    - Create, update, delete pages
    - Search pages and spaces
    - Link JIRA issues to pages
    - Create formatted report pages from JIRA data

    Workflow Examples:
    1. "Generate a sprint report for board 1" → Sprint analysis with metrics
    2. "Show me the workload for project SCRUM" → Who's working on what
    3. "Create a bug report for SCRUM project" → Bug analysis and trends
    4. "Generate velocity report and publish to Confluence" → Multi-step workflow
    5. "Find aging issues in SCRUM older than 45 days" → Identify stale work

    When generating reports:
    - Always get board IDs first if needed (use get_jira_boards)
    - Provide clear, actionable insights
    - Offer to publish reports to Confluence if useful
    - Suggest follow-up actions based on report data

    For assignments (GDPR compliant):
    - Use 'me' for self-assignment
    - Get assignable users first, then use displayName or accountId"""
)

# Create user proxy agent
user_proxy = autogen.UserProxyAgent(
    name="User",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    code_execution_config=False,
    function_map={
        # Basic JIRA operations
        "create_jira_issue": create_jira_issue,
        "get_jira_issue": get_jira_issue,
        "search_jira_issues": search_jira_issues,
        "update_jira_issue": update_jira_issue,
        "add_jira_comment": add_jira_comment,
        "transition_jira_issue": transition_jira_issue,
        "assign_jira_issue": assign_jira_issue,
        "get_assignable_users": get_assignable_users,
        "get_jira_boards": get_jira_boards,
        # Report functions
        "generate_sprint_report": generate_sprint_report,
        "generate_project_summary": generate_project_summary,
        "generate_user_workload_report": generate_user_workload_report,
        "generate_velocity_report": generate_velocity_report,
        "generate_issue_aging_report": generate_issue_aging_report,
        "generate_bug_report": generate_bug_report,
        "generate_custom_report": generate_custom_report,
        # Confluence operations
        "create_confluence_page": create_confluence_page,
        "get_confluence_page": get_confluence_page,
        "update_confluence_page": update_confluence_page,
        "delete_confluence_page": delete_confluence_page,
        "get_confluence_spaces": get_confluence_spaces,
        "search_confluence_pages": search_confluence_pages,
        "link_jira_to_confluence": link_jira_to_confluence,
        "create_report_in_confluence": create_report_in_confluence,
    }
)

# Register all functions
functions_to_register = [
    (create_jira_issue, "Create a new JIRA issue"),
    (get_jira_issue, "Get JIRA issue details"),
    (search_jira_issues, "Search JIRA issues using JQL"),
    (update_jira_issue, "Update a JIRA issue"),
    (add_jira_comment, "Add a comment to a JIRA issue"),
    (transition_jira_issue, "Transition a JIRA issue"),
    (assign_jira_issue, "Assign a JIRA issue to a user"),
    (get_assignable_users, "Get list of assignable users"),
    (get_jira_boards, "Get list of JIRA boards"),
    (generate_sprint_report, "Generate comprehensive sprint report with metrics and analysis"),
    (generate_project_summary, "Generate overall project summary with status distribution"),
    (generate_user_workload_report, "Generate workload report showing current assignments"),
    (generate_velocity_report, "Generate velocity report for recent sprints"),
    (generate_issue_aging_report, "Generate report of aging/stale issues"),
    (generate_bug_report, "Generate comprehensive bug analysis report"),
    (generate_custom_report, "Generate custom report using JQL query"),
    (create_confluence_page, "Create a new Confluence page"),
    (get_confluence_page, "Get Confluence page details"),
    (update_confluence_page, "Update a Confluence page"),
    (delete_confluence_page, "Delete a Confluence page"),
    (get_confluence_spaces, "Get list of Confluence spaces"),
    (search_confluence_pages, "Search Confluence pages"),
    (link_jira_to_confluence, "Link JIRA issue to Confluence page"),
    (create_report_in_confluence, "Create formatted Confluence page from JIRA report"),
]

for func, description in functions_to_register:
    autogen.register_function(
        func,
        caller=assistant,
        executor=user_proxy,
        description=description
    )


def main():
    """Main function to run the JIRA agent"""

    print("=== JIRA & Confluence AI Agent with Advanced Reporting ===\n")

    # Example tasks
    tasks = [
        # Basic JIRA
        "Create a task in SCRUM: Implement user authentication",
        "Search for all bugs in SCRUM project",
        "Get details of SCRUM-1",

        # Reports
        "Get list of boards for project SCRUM",
        "Generate a sprint report for the active sprint on board 1",
        "Show me a project summary for SCRUM",
        "Generate a workload report for SCRUM project",
        "Create a velocity report for board 1 analyzing last 3 sprints",
        "Find all aging issues in SCRUM older than 45 days",
        "Generate a comprehensive bug report for SCRUM",
        "Create a custom report for all high priority open issues in SCRUM",

        # Confluence integration
        "Generate a sprint report and publish it to Confluence space TEAM",
        "Create a project summary report and save it to Confluence",
    ]

    print("Available example tasks:")
    for i, task in enumerate(tasks, 1):
        print(f"{i}. {task}")

    print("\nYou can also type your own request or 'exit' to quit.\n")

    while True:
        user_input = input("Your request: ").strip()

        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        if user_input.isdigit():
            idx = int(user_input) - 1
            if 0 <= idx < len(tasks):
                user_input = tasks[idx]
            else:
                print("Invalid task number")
                continue

        if not user_input:
            continue

        try:
            user_proxy.initiate_chat(
                assistant,
                message=user_input
            )
            print("\n" + "=" * 50 + "\n")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    print("JIRA AI Agent with Advanced Reporting")
    print("=" * 50)
    print("\nNew Features:")
    print("✓ Sprint Reports - Completion rates, assignee distribution")
    print("✓ Project Summary - Overall health metrics")
    print("✓ User Workload - Current assignments and distribution")
    print("✓ Velocity Reports - Team performance trends")
    print("✓ Issue Aging - Identify stale issues")
    print("✓ Bug Reports - Bug analysis and trends")
    print("✓ Custom Reports - Use any JQL query")
    print("✓ Confluence Integration - Publish reports as pages")
    print("\nMake sure you have:")
    print("1. Ollama running (ollama serve)")
    print("2. Model downloaded (ollama pull qwen2.5)")
    print("3. JIRA credentials configured")
    print("4. Confluence access configured\n")

    main()