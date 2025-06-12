import React from "react"; export default function PersonaSelector({ activePersona, onPersonaChange, className = "" }) { return <div className={className}>Persona Selector - {activePersona}</div>; }
