"use client";
import { useState, useEffect } from "react";
import { api, Property } from "@/lib/api";
import PropertyView from "@/components/PropertyView";

export default function Home() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [selected, setSelected] = useState<Property | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", address: "" });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getProperties().then(p => { setProperties(p); setLoading(false); });
  }, []);

  const createProperty = async () => {
    if (!form.name || !form.address) return;
    const p = await api.createProperty(form.name, form.address);
    setProperties(prev => [p, ...prev]);
    setSelected(p);
    setCreating(false);
    setForm({ name: "", address: "" });
  };

  const updateSelected = (p: Property) => {
    setSelected(p);
    setProperties(prev => prev.map(x => x.id === p.id ? p : x));
  };

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Sidebar */}
      <div style={{
        width: 280, borderRight: "1px solid var(--border)",
        display: "flex", flexDirection: "column", flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: "20px 16px", borderBottom: "1px solid var(--border)" }}>
          <div className="heading" style={{ fontSize: 18, fontWeight: 800, color: "var(--amber)" }}>
            ContextHaus
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 2 }}>
            Property Context Engine
          </div>
        </div>

        {/* New Property Button */}
        <div style={{ padding: "12px 16px", borderBottom: "1px solid var(--border)" }}>
          <button
            onClick={() => setCreating(!creating)}
            style={{
              width: "100%", padding: "8px 12px", background: "var(--amber)",
              color: "#000", border: "none", cursor: "pointer", fontFamily: "inherit",
              fontSize: 12, fontWeight: 600, letterSpacing: "0.05em",
            }}
          >
            + NEW PROPERTY
          </button>

          {creating && (
            <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6 }} className="fade-in">
              <input
                placeholder="Property name"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                style={{
                  background: "var(--surface)", border: "1px solid var(--border)",
                  color: "var(--text)", padding: "6px 8px", fontFamily: "inherit",
                  fontSize: 12, outline: "none", width: "100%",
                }}
              />
              <input
                placeholder="Address"
                value={form.address}
                onChange={e => setForm(f => ({ ...f, address: e.target.value }))}
                style={{
                  background: "var(--surface)", border: "1px solid var(--border)",
                  color: "var(--text)", padding: "6px 8px", fontFamily: "inherit",
                  fontSize: 12, outline: "none", width: "100%",
                }}
              />
              <button
                onClick={createProperty}
                style={{
                  background: "var(--surface)", border: "1px solid var(--amber)",
                  color: "var(--amber)", padding: "6px 8px", cursor: "pointer",
                  fontFamily: "inherit", fontSize: 12,
                }}
              >
                CREATE →
              </button>
            </div>
          )}
        </div>

        {/* Property List */}
        <div style={{ flex: 1, overflowY: "auto" }}>
          {loading && (
            <div style={{ padding: 16, color: "var(--text-muted)" }}>Loading...</div>
          )}
          {properties.map(p => (
            <div
              key={p.id}
              onClick={() => setSelected(p)}
              style={{
                padding: "12px 16px", cursor: "pointer",
                borderBottom: "1px solid var(--border)",
                background: selected?.id === p.id ? "var(--surface)" : "transparent",
                borderLeft: selected?.id === p.id ? "2px solid var(--amber)" : "2px solid transparent",
                transition: "all 0.15s",
              }}
            >
              <div style={{ fontWeight: 500, color: "var(--text)", fontSize: 12 }}>{p.name}</div>
              <div style={{ color: "var(--text-muted)", fontSize: 11, marginTop: 2 }}>{p.address}</div>
              <div style={{ marginTop: 4 }}>
                <span style={{
                  fontSize: 10, padding: "2px 6px",
                  background: p.context_md ? "rgba(74,222,128,0.1)" : "rgba(107,104,96,0.2)",
                  color: p.context_md ? "var(--green)" : "var(--text-muted)",
                }}>
                  {p.context_md ? "● LIVE" : "○ EMPTY"}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", color: "var(--text-muted)", fontSize: 10 }}>
          Powered by Gemini 2.5 · Tavily · Pioneer
        </div>
      </div>

      {/* Main Panel */}
      <div style={{ flex: 1, overflow: "hidden" }}>
        {selected ? (
          <PropertyView property={selected} onUpdate={updateSelected} />
        ) : (
          <div style={{
            height: "100%", display: "flex", alignItems: "center",
            justifyContent: "center", flexDirection: "column", gap: 12,
          }}>
            <div className="heading" style={{ fontSize: 32, fontWeight: 800, color: "var(--border)" }}>
              SELECT A PROPERTY
            </div>
            <div style={{ color: "var(--text-muted)" }}>
              or create one to get started
            </div>
          </div>
        )}
      </div>
    </div>
  );
}