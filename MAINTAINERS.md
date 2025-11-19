# Maintainers

## Current Maintainers

| Name | GitHub | Role | Focus Areas |
|------|--------|------|-------------|
| [Maintainer Name] | [@github-handle] | Lead Maintainer | Overall direction, releases, security |

## Responsibilities

### All Maintainers
- Review and merge pull requests
- Triage and respond to issues
- Follow the Code of Conduct and enforce it
- Keep dependencies updated
- Maintain documentation
- Release new versions

### Lead Maintainer
- Overall project direction and strategy
- Final decision authority on architectural changes
- Coordinate security releases
- Publish releases to package repositories

## Becoming a Maintainer

We welcome contributions! If you're interested in becoming a maintainer:

1. Demonstrate sustained contribution to the project
2. Show understanding of the codebase and project goals
3. Discuss with current maintainers about your interest
4. Be nominated and approved by current maintainers

## Process for Decisions

### Minor Changes
- Code reviews and approval by any maintainer
- Can be merged immediately after approval
- Examples: documentation, tests, bug fixes

### Major Changes
- Discussion in GitHub issues
- Code review by multiple maintainers
- Consideration of impact on users
- May require RFC (Request for Comments)

### Releases
- Coordinated by lead maintainer
- Follow semantic versioning
- Update CHANGELOG.md
- Tag releases in git
- Push to package repositories

## Release Process

1. **Version Bump**: Update version number in relevant files
2. **Changelog**: Update CHANGELOG.md with all changes
3. **Testing**: Run full test suite
4. **Review**: Have at least one other maintainer review
5. **Tag**: Create git tag: `git tag vX.Y.Z`
6. **Publish**: Push tag and publish to PyPI/relevant repositories
7. **Announce**: Create GitHub release with changelog

## Maintenance Schedule

- **Code reviews**: Best effort, typically within 2-5 business days
- **Issue triage**: Weekly
- **Dependency updates**: Monthly
- **Releases**: As needed, minimum quarterly security reviews

## Communication

- Primary: GitHub Issues and Pull Requests
- Discussion: GitHub Discussions
- Security: See SECURITY.md for private reporting

## Conflict Resolution

If there's disagreement between maintainers:

1. **Discussion**: Open, respectful discussion on the relevant GitHub issue/PR
2. **Consensus**: Try to find a solution that satisfies all parties
3. **Arbitration**: Lead maintainer makes final decision if consensus can't be reached
4. **Escalation**: Can be escalated to Code of Conduct committee if necessary

## Stepping Down

If a maintainer needs to step down:

1. Give notice to other maintainers
2. Help transition responsibilities
3. Update MAINTAINERS.md
4. Archive private access/keys

## Resources for Maintainers

- [GitHub Docs - Maintaining Open Source](https://docs.github.com/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Open Source Community Best Practices](https://opensource.org/community)

## Security

- Never commit secrets or credentials
- Keep dependencies up to date
- Review security advisories regularly
- Use environment variables for sensitive configuration
- Follow SECURITY.md guidelines

---

## Special Thanks

We're grateful to all contributors and community members who help make this project better!

If you have questions about maintenance or want to get more involved, please reach out through GitHub Issues or Discussions.
