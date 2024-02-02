# Version 1.3.4 (5/15/21)

### Site updates

- Changed the encouraged word count from 300 to 150

### Bugs fixed

- Show line breaks in reviews

# Version 1.3.3 (5/7/21)

### Site updates

- Course dropdown
- (Main reason why this update exists) Added review drive banner

### Bugs fixed

### Dev-related updates

- Include commit message in Discord notifications
- Temporarily limited the range of allowed versions for `pylint` in `requirements.txt`

# Version 1.3.2 (4/13/21)

### Site updates

- Reordered emojis on reviews
- Adjusted FAQ
- Show number of reviews and comments (as separate numbers)
- Changed reviews to show upvotes/downvotes separately
- Something with ads?

### Bugs fixed

# Version 1.3.1 (3/21/21)

### Site updates

- Add banner ad to central browse page

### Bugs fixed

- Several `precommit.sh` bugfixes
- GitHub Actions now stops on error (before it'd run anyways and say no issues)
- Fixed bug where edit review wouldn't update hours

### Dev-related updates

- Removed `chart.js` from `package.json`
- Upgraded Python to 3.9.2
- Added a _lot_ of tests

# Version 1.3 (3/10/21)

### Site updates

- Added banner to our GoFundMe on browse page
- Added AdSense script (actual ads yet to be set up)
- Added social media links to sidebar
- Review collapser
- Sort ascending and descending on subdepartment page when browsing
- Placeholder box on a course page when it's not being taught this semester
- Word count progress bar on review create/update page

### Bugs fixed

- Fixed TOS not properly linking to Privacy Policy
- Extra form validation for graduation year
- Prevent users from submitting duplicate reviews
- Other various bugfixes...

### Dev-related updates

- Fixed various minor bugs with GAE deploy
- Optimizations to `precommit` and the instructor page view
- Added new D&M members to site
- Deploys now send notifications to `#builds` in the Discord server
- Removed django-silk from deploys (have yet to drop data tables, but they won't accrue more unnecessary data)

# Version 1.2

### Site updates

- Added edit/delete review functionality
- Added messages with feedback upon editing/deleting review
- Site should redirect user to previous page upon login
- Fixed 404 error for privacy policy in FAQ

### Dev-related updates

- Improved documentation
- Fleshed out Markdown templates for issues/PRs
- Added new members to site!
- GitHub Actions (essentially) finalized - finally moving away from Travis!
- This cool new wiki!

# Versions 1.0.0-1.1.3

Will update later
