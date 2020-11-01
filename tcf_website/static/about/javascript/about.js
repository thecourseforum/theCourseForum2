import { showHistory, showCurrentTeam, showPastContributors, showSponsors } from "../javascript/switch-subcontent.js";

document.getElementById('tCF-history-btn').addEventListener('click', showHistory, false);
document.getElementById('tCF-current-team-btn').addEventListener('click', showCurrentTeam, false);
document.getElementById('tCF-past-contributors-btn').addEventListener('click', showPastContributors, false);
document.getElementById('tCF-sponsors-btn').addEventListener('click', showSponsors, false);
