import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';

/**
 * OAuth callback handler.
 *
 * After a social login (Google/GitHub/LinkedIn), Supabase redirects the user
 * back to this page. The Supabase client automatically picks up the auth
 * tokens from the URL hash. This component waits for the session to resolve,
 * then navigates to the appropriate portal.
 */
export default function AuthCallback() {
  const navigate = useNavigate();
  const { user, loading, role } = useAuth();

  useEffect(() => {
    if (loading) return;

    if (user) {
      // User is authenticated — route based on their stored role
      if (role === 'recruiter') {
        navigate('/recruiter', { replace: true });
      } else if (role === 'student') {
        navigate('/student', { replace: true });
      } else {
        // First-time social login — redirect to login page to pick a role
        navigate('/login?pick_role=true', { replace: true });
      }
    } else {
      // No session resolved — something went wrong, go back to login
      navigate('/login', { replace: true });
    }
  }, [user, loading, role, navigate]);

  return (
    <div className="layout-container max-w-lg mx-auto py-24 text-center">
      <div className="card-premium p-12 flex flex-col items-center gap-4">
        {/* Animated spinner */}
        <div
          className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
          style={{ borderColor: 'var(--color-accent)', borderTopColor: 'transparent' }}
        />
        <p className="text-sm font-semibold" style={{ color: 'var(--color-text-secondary)' }}>
          Completing sign-in...
        </p>
      </div>
    </div>
  );
}
