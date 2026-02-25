# Stone Ranch Command Center - TODO & Ideas

## High Priority
- [ ] Fix world news sources - verify Reuters and NYT are loading properly
- [ ] Verify chores persistence works across Pi reboots (data.json)
- [x] Add chores to dashboard - FIXED: config used "frequency" but app expected "schedule"
- [x] Add source display for world news (like tech news has) - ALREADY IMPLEMENTED

## Medium Priority
- [ ] Bills/expenses tracker - scrape credit cards or manually input monthly bills for spending overview
- [ ] Calendar integration (Google Calendar, Outlook)
- [ ] Add more news sources (academic papers for future)
- [ ] Make weather location configurable via UI (not just config.py)

## Low Priority / Ideas
- [ ] Morning briefing - automatic summary of weather, chores, news headlines
- [ ] Family grocery list with local storage
- [ ] Meal planner for the week
- [ ] Package tracking integration
- [ ] GitHub notifications widget
- [ ] Stocks - add more, allow user to configure via UI
- [ ] Add "last updated" timestamps to widgets
- [ ] Dark/light theme toggle
- [ ] Add more creative features - feel free to experiment!

## Known Issues
- Weather API only provides hourly data from midnight UTC - workaround with timezone param is working
- News RSS feeds can be finicky with date parsing
- Debug mode disabled to prevent auto-reload crashes

## User Requests (from conversation)
- Want something "they WANT to wake up and check every morning"
- Reduce mental load by bringing weather → reddit → news → instagram into one place
- Focus on meaningful value for household
- Keep it simple but useful
