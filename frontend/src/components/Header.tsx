import { Link, useLocation } from 'react-router-dom';
import { Activity } from 'lucide-react';

export default function Header() {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path ? 'active' : '';

  return (
    <header className="header">
      <div className="header-inner">
        <Link to="/" className="header-logo">
          <Activity size={22} />
          Derma<span>Twin</span>
          <div className="header-logo-dot" />
        </Link>

        <nav className="header-nav">
          <Link to="/" className={isActive('/')}>Analyze</Link>
          <Link to="/results" className={isActive('/results')}>Results</Link>
          <Link to="/dashboard" className={isActive('/dashboard')}>Dashboard</Link>
        </nav>
      </div>
    </header>
  );
}
