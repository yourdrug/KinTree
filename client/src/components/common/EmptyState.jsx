/**
 * components/common/EmptyState.jsx
 *
 * Заглушка для пустых списков.
 * Используется в Dashboard, Explore.
 */

export default function EmptyState({ emoji = "🔍", title, description }) {
  return (
    <div className="text-center py-20">
      <div className="text-6xl mb-5">{emoji}</div>
      <h3 className="font-serif text-xl font-semibold text-foreground mb-2">{title}</h3>
      {description && (
        <p className="text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
