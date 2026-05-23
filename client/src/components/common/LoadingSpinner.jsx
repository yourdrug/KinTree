/**
 * components/common/LoadingSpinner.jsx
 */

export default function LoadingSpinner({ fullScreen = false }) {
  const spinner = (
    <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
  );

  if (!fullScreen) return spinner;

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-background">
      {spinner}
    </div>
  );
}
