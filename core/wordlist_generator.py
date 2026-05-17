import os
import string
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

log = get_logger("wordlist_generator")

COMMON_PASSWORDS = [
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "welcome",
    "hello", "charlie", "donald", "admin", "admin123", "root", "toor",
    "P@ssw0rd", "Password1!", "Welcome1", "ChangeMe123",
]

COMMON_USERNAMES = [
    "admin", "root", "user", "test", "guest", "info", "adm", "mysql",
    "postgres", "oracle", "ftp", "www", "webmaster", "support", "operator",
    "backup", "sysadmin", "developer", "manager", "service", "nagios",
    "tomcat", "jenkins", "ubuntu", "deploy", "ansible", "vagrant",
]

PATTERNS = {
    "company_year": "{name}{year}",
    "company_year_num": "{name}{year}1",
    "company_symbol": "{name}{symbol}",
    "name_year": "{first}{last}{year}",
    "name_symbol": "{first}{last}{symbol}",
    "season_year": "{season}{year}",
    "month_year": "{month}{year}",
}

SYMBOLS = ["!", "@", "#", "$", "%", "&", "*", "1", "123", "123!"]
SEASONS = ["spring", "summer", "fall", "winter"]
MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]


class WordlistGenerator:
    """Smart wordlist generator based on target information."""

    def __init__(self):
        self.common_passwords = COMMON_PASSWORDS
        self.common_usernames = COMMON_USERNAMES
        self.patterns = PATTERNS
        self.symbols = SYMBOLS
        self.seasons = SEASONS
        self.months = MONTHS
        self._generated = []

    def generate_from_target(self, target_info):
        wordlist = set()
        name = target_info.get("name", "").lower().strip()
        domain = target_info.get("domain", "").lower().strip()
        year = str(datetime.now().year)
        prev_year = str(datetime.now().year - 1)

        if name:
            name_clean = "".join(c for c in name if c.isalnum())
            wordlist.add(name_clean)
            wordlist.add(name_clean.capitalize())
            wordlist.add(name_clean.upper())
            for sym in self.symbols:
                wordlist.add(f"{name_clean}{sym}")
                wordlist.add(f"{name_clean.capitalize()}{sym}")
            wordlist.add(f"{name_clean}{year}")
            wordlist.add(f"{name_clean}{prev_year}")
            wordlist.add(f"{name_clean}{year}!")

        if domain:
            domain_clean = domain.split(".")[0]
            wordlist.add(domain_clean)
            wordlist.add(domain_clean.capitalize())
            for sym in self.symbols:
                wordlist.add(f"{domain_clean}{sym}")
            wordlist.add(f"{domain_clean}{year}")

        for season in self.seasons:
            wordlist.add(f"{season}{year}")
            wordlist.add(f"{season.capitalize()}{year}")
            if name:
                wordlist.add(f"{name}{season}{year}")

        for month in self.months:
            wordlist.add(f"{month}{year}")
            wordlist.add(f"{month.capitalize()}{year}")

        wordlist.update(self.common_passwords)
        self._generated = sorted(wordlist)
        return self._generated

    def generate_usernames(self, target_info):
        usernames = set()
        first = target_info.get("first_name", "").lower()
        last = target_info.get("last_name", "").lower()
        domain = target_info.get("domain", "").lower().split(".")[0]

        usernames.update(self.common_usernames)

        if first and last:
            usernames.add(f"{first}.{last}")
            usernames.add(f"{first}{last}")
            usernames.add(f"{first[0]}{last}")
            usernames.add(f"{first}{last[0]}")
            usernames.add(f"{last}.{first}")
            usernames.add(f"{last}{first}")
            usernames.add(f"{first}_{last}")

        if domain:
            usernames.add(f"admin@{domain}")
            usernames.add(f"info@{domain}")
            usernames.add(f"support@{domain}")
            usernames.add(f"{domain}_admin")

        return sorted(usernames)

    def generate_mutation(self, base_word):
        mutations = set()
        word = base_word.lower()
        mutations.add(word)
        mutations.add(word.capitalize())
        mutations.add(word.upper())

        leet = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        leeted = "".join(leet.get(c, c) for c in word)
        mutations.add(leeted)
        mutations.add(leeted.capitalize())

        for sym in self.symbols:
            mutations.add(f"{word}{sym}")
            mutations.add(f"{word.capitalize()}{sym}")
            mutations.add(f"{sym}{word}")

        year = str(datetime.now().year)
        mutations.add(f"{word}{year}")
        mutations.add(f"{word}{year}!")
        mutations.add(f"{leeted}{year}")

        return sorted(mutations)

    def save_to_file(self, wordlist, filepath):
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            for word in wordlist:
                f.write(f"{word}\n")
        return str(path)

    def generate_custom(self, base_words, min_len=4, max_len=16):
        wordlist = set()
        for word in base_words:
            w = word.lower().strip()
            if min_len <= len(w) <= max_len:
                wordlist.add(w)
                wordlist.add(w.capitalize())
                mutations = self.generate_mutation(w)
                wordlist.update(mutations)
        self._generated = sorted(wordlist)
        return self._generated

    def get_stats(self):
        return {
            "total_generated": len(self._generated),
            "common_passwords": len(self.common_passwords),
            "common_usernames": len(self.common_usernames),
        }

    def format_for_prompt(self, target_info=None):
        lines = ["**Smart Wordlist Generator:**"]
        lines.append(f"  Common passwords: {len(self.common_passwords)}")
        lines.append(f"  Common usernames: {len(self.common_usernames)}")
        lines.append(f"  Mutation patterns: {len(self.patterns)}")
        if target_info:
            lines.append(f"  Target: {target_info.get('name', 'N/A')} / {target_info.get('domain', 'N/A')}")
        lines.append(f"  Use: `/wordlist generate [target_info]`")
        return "\n".join(lines)
