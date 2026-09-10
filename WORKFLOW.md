# GitHub Team Workflow

## 1. Branching Strategy

Our team keeps the `main` branch clean and releasable at all times.

All new work is developed in separate feature branches using the following naming convention:

`feature/[short-description]`

For example:

`feature/data-ingestion`

Feature branches allow team members to work independently without affecting the stable main branch.

Once the work is reviewed and merged into `main`, the feature branch is deleted to keep the repository organized.

## 2. Commit Message Convention

Our team follows a consistent commit message format:

`[type]: [description]`

The commit types used by our team are:

- `feat` - New feature or capability
- `fix` - Bug fix
- `docs` - Documentation changes
- `refactor` - Code restructuring without changing behavior
- `chore` - Maintenance or configuration changes

Examples:

- `feat: add data validation workflow`
- `docs: document team github workflow`
- `fix: correct missing value calculation`

Consistent commit messages make the project history easier to understand and enable automated changelog generation.

## 3. Pull Request Review Process

All changes must be submitted through a Pull Request before being merged into `main`.

Our process is:

1. Create a feature branch from `main`.
2. Make and commit the required changes.
3. Push the branch to GitHub.
4. Open a Pull Request targeting `main`.
5. Link the related GitHub issue.
6. Request review from at least one teammate.
7. Address review feedback.
8. Merge only after receiving at least one approval.
9. Delete the feature branch after merging.

Code review focuses on:

- Correctness
- Code clarity
- Data integrity
- Test coverage

Commit messages are also reviewed to ensure they follow the team's convention.

## 4. GitHub Issue Tracking

Every feature or bug fix starts with a GitHub issue.

Each issue should contain:

- A clear action-oriented title
- A description explaining the objective and context
- At least one appropriate label
- An assignee responsible for completing the work

Issues provide a clear record of what needs to be done and who is responsible for it.

The corresponding issue is closed when its Pull Request is successfully merged.

## 5. Standard Contribution Workflow

A team member contributing a new feature should:

1. Pull the latest changes from `main`.
2. Create a new feature branch.
3. Create or identify the corresponding GitHub issue.
4. Make the changes on the feature branch.
5. Commit changes using the team's commit convention.
6. Push the feature branch to GitHub.
7. Open a Pull Request targeting `main`.
8. Link the issue using `Closes #[issue-number]`.
9. Address code review feedback.
10. Merge the Pull Request after approval.
11. Delete the feature branch.