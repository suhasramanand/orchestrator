import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import JobCreateForm from './components/JobCreateForm';
import Analytics from './components/Analytics';
import './App.css';

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation();
  const isActive = location.pathname === to || (to === '/' && location.pathname === '/');
  return (
    <Link to={to} className={isActive ? 'active' : ''}>
      {children}
    </Link>
  );
}

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <div className="container">
            <h1>Job Orchestration</h1>
            <nav>
              <NavLink to="/">Jobs</NavLink>
              <NavLink to="/create">Create</NavLink>
              <NavLink to="/analytics">Analytics</NavLink>
            </nav>
          </div>
        </header>

        <main className="app-main">
          <div className="container">
            <Routes>
              <Route path="/" element={<JobList />} />
              <Route path="/create" element={<JobCreateForm />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/jobs/:jobId" element={<JobDetail />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;

