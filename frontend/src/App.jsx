import React, { useState, useEffect } from "react";
import { Navbar } from "./components/Navbar";
import { HeroBanner } from "./components/HeroBanner";
import { MovieCard } from "./components/MovieCard";
import { AIAssistantModal } from "./components/AIAssistantModal";
import { OnboardingModal } from "./components/OnboardingModal";
import { MovieDetailModal } from "./components/MovieDetailModal";
import { getPopularMovies, getForYouFeed, searchMovies } from "./api/client";
import { Sparkles } from "lucide-react";

export function App() {
  const [popular, setPopular] = useState([]);
  const [feed, setFeed] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [loading, setLoading] = useState(true);

  const [aiOpen, setAiOpen] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      getPopularMovies(20).then(setPopular).catch(console.error),
      getForYouFeed().then(setFeed).catch(console.error)
    ]).finally(() => setLoading(false));
  };

  const handleSearchSubmit = async (query) => {
    try {
      setLoading(true);
      const results = await searchMovies(query, 24);
      setSearchResults({ query, items: results });
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setLoading(false);
    }
  };

  const heroMovie = popular.length > 0 ? popular[0] : null;

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Sticky Header Navigation */}
      <Navbar
        onOpenAI={() => setAiOpen(true)}
        onOpenOnboarding={() => setOnboardingOpen(true)}
        onSearchSubmit={handleSearchSubmit}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1, paddingBottom: "48px", paddingTop: "16px" }}>
        {loading ? (
          <div style={{ textAlign: "center", padding: "80px 24px", color: "var(--text-secondary)" }}>
            <Sparkles size={40} className="pulse-glow" style={{ marginBottom: "16px" }} />
            <p style={{ fontSize: "1.1rem", fontWeight: "500" }}>Loading CineSense Recommendation Feed...</p>
          </div>
        ) : searchResults ? (
          /* Search Results View */
          <div style={{ padding: "0 24px", marginTop: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
              <h2 style={{ fontSize: "1.5rem", fontWeight: "700" }}>
                Search Results for <span className="gradient-text">"{searchResults.query}"</span>
              </h2>
              <button
                onClick={() => setSearchResults(null)}
                style={{
                  background: "rgba(255,255,255,0.08)",
                  border: "1px solid var(--border-glass)",
                  borderRadius: "var(--radius-full)",
                  padding: "6px 16px",
                  color: "#fff",
                  cursor: "pointer"
                }}
              >
                Clear Search
              </button>
            </div>

            <div style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
              gap: "20px"
            }}>
              {searchResults.items.map((m) => (
                <MovieCard key={m.id} movie={m} onSelectMovie={setSelectedMovie} />
              ))}
            </div>
          </div>
        ) : (
          /* Default Feed View */
          <>
            {/* Spotlight Banner */}
            {heroMovie && <HeroBanner movie={heroMovie} onSelectMovie={setSelectedMovie} />}

            {/* Recommendation Rows */}
            <div style={{ padding: "0 24px", display: "flex", flexDirection: "column", gap: "36px", marginTop: heroMovie ? "0px" : "24px" }}>
              {feed?.rows?.map((row, idx) => (
                <section key={idx}>
                  <h2 style={{ fontSize: "1.4rem", fontWeight: "700", marginBottom: "16px", letterSpacing: "-0.3px" }}>
                    {row.title}
                  </h2>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(175px, 1fr))",
                    gap: "20px"
                  }}>
                    {row.items?.map((m) => (
                      <MovieCard key={m.id} movie={m} onSelectMovie={setSelectedMovie} />
                    ))}
                  </div>
                </section>
              ))}

              {/* Top Rated Classics Row */}
              {popular.length > 1 && (
                <section>
                  <h2 style={{ fontSize: "1.4rem", fontWeight: "700", marginBottom: "16px" }}>
                    Top Rated Classics
                  </h2>
                  <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(175px, 1fr))",
                    gap: "20px"
                  }}>
                    {popular.slice(1, 13).map((m) => (
                      <MovieCard key={m.id} movie={m} onSelectMovie={setSelectedMovie} />
                    ))}
                  </div>
                </section>
              )}
            </div>
          </>
        )}
      </main>

      {/* Modals & Drawers */}
      <AIAssistantModal
        isOpen={aiOpen}
        onClose={() => setAiOpen(false)}
        onSelectMovie={(m) => {
          setAiOpen(false);
          setSelectedMovie(m);
        }}
      />

      <OnboardingModal
        isOpen={onboardingOpen}
        onClose={() => setOnboardingOpen(false)}
        onComplete={() => {
          setOnboardingOpen(false);
          loadData();
        }}
      />

      <MovieDetailModal
        movie={selectedMovie}
        onClose={() => setSelectedMovie(null)}
        onSelectMovie={setSelectedMovie}
      />
    </div>
  );
}

export default App;
