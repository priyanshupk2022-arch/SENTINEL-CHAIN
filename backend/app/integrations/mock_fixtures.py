class MockFixtureManager:
    @staticmethod
    def get_fixture(url: str) -> str:
        if "reddit.com" in url:
            return "<html><body>Reddit Thread Fixture</body></html>"
        elif "g2.com" in url:
            return "<html><body>G2 Review Fixture</body></html>"
        elif "x.com" in url or "twitter.com" in url:
            return "<html><body>Twitter Feed Fixture</body></html>"
        elif "github.com" in url:
            return "<html><body>GitHub Issues Fixture</body></html>"
        elif "producthunt.com" in url:
            return "<html><body>ProductHunt Fixture</body></html>"
        return "<html><body>Generic Mock Fixture</body></html>"
