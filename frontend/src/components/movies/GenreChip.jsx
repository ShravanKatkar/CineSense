import React from "react";
import { C } from "../../constants/theme";

export default function GenreChip({ genre, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`genre-chip${active ? " active" : ""}`}
      style={{
        background: active ? C.accentDim : "transparent",
        color: active ? C.accent : C.muted,
        border: "none",
        cursor: "pointer",
        fontFamily: "'Work Sans', sans-serif",
      }}
    >
      {genre}
    </button>
  );
}
