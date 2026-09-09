import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ROUTES, type RouteId } from './navigation';

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  onNavigate: (id: RouteId) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ open, onClose, onNavigate }) => {
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const matches = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return ROUTES;
    return ROUTES.filter(
      (route) =>
        route.label.toLowerCase().includes(needle) ||
        route.description.toLowerCase().includes(needle) ||
        route.group.toLowerCase().includes(needle),
    );
  }, [query]);

  useEffect(() => {
    if (open) {
      setQuery('');
      setActiveIndex(0);
      // Focus after paint so the field is ready for immediate typing.
      window.requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  if (!open) return null;

  const commit = (id: RouteId) => {
    onNavigate(id);
    onClose();
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      onClose();
      return;
    }
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((index) => (matches.length ? (index + 1) % matches.length : 0));
      return;
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((index) => (matches.length ? (index - 1 + matches.length) % matches.length : 0));
      return;
    }
    if (event.key === 'Enter' && matches[activeIndex]) {
      event.preventDefault();
      commit(matches[activeIndex].id);
    }
  };

  return (
    <div
      className="palette-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="palette" role="dialog" aria-modal="true" aria-label="Command palette">
        <input
          ref={inputRef}
          className="palette-input"
          type="text"
          placeholder="Jump to a module…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Search modules"
        />

        <div className="palette-list">
          {matches.length === 0 ? (
            <p className="text-sm muted" style={{ padding: '14px 12px' }}>
              No module matches “{query}”.
            </p>
          ) : (
            matches.map((route, index) => {
              const Icon = route.icon;
              return (
                <button
                  key={route.id}
                  type="button"
                  className={`palette-item${index === activeIndex ? ' is-active' : ''}`}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => commit(route.id)}
                >
                  <Icon size={16} />
                  <span className="grow">
                    <span style={{ fontWeight: 570 }}>{route.label}</span>
                    <span className="text-xs muted" style={{ display: 'block' }}>
                      {route.description}
                    </span>
                  </span>
                  <span className="text-xs faint">{route.group}</span>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
