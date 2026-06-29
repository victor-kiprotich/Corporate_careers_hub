import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation, useNavigate } from 'react-router-dom';
import { Bookmark, Building, Briefcase, Search, Sun, Moon } from 'lucide-react'; // Added Sun and Moon icons
import './App.css';

// Create a context for saved jobs
const SavedJobsContext = createContext();

const SavedJobsProvider = ({ children }) => {
  const [savedJobIds, setSavedJobIds] = useState(() => {
    const localData = localStorage.getItem('savedJobIds');
    return localData ? JSON.parse(localData) : [];
  });

  useEffect(() => {
    localStorage.setItem('savedJobIds', JSON.stringify(savedJobIds));
  }, [savedJobIds]);

  const toggleSavedJob = (jobId) => {
    setSavedJobIds(prevIds =>
      prevIds.includes(jobId) ? prevIds.filter(id => id !== jobId) : [...prevIds, jobId]
    );
  };

  return (
    <SavedJobsContext.Provider value={{ savedJobIds, toggleSavedJob }}>
      {children}
    </SavedJobsContext.Provider>
  );
};

// Create a context for Light/Dark Theme
const ThemeContext = createContext();

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    const localTheme = localStorage.getItem('theme');
    return localTheme ? localTheme : 'light';
  });

  useEffect(() => {
    localStorage.setItem('theme', theme);
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

const Navbar = () => {
  const location = useLocation();
  const { theme, toggleTheme } = useContext(ThemeContext); // Consume theme context

  return (
    <nav className="navbar bg-indigo-700 text-white p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="navbar-brand text-2xl font-bold">CORPORATE CAREERS HUB</Link>
        
        <div className="flex items-center space-x-6">
          <ul className="nav-links flex space-x-4">
            <li><Link to="/find-jobs" className={`text-white hover:text-indigo-200 ${location.pathname === '/find-jobs' || location.pathname === '/' ? 'font-bold border-b-2 border-indigo-200' : ''}`}>Find Jobs</Link></li>
            <li><Link to="/companies" className={`text-white hover:text-indigo-200 ${location.pathname === '/companies' ? 'font-bold border-b-2 border-indigo-200' : ''}`}>Companies</Link></li>
            <li><Link to="/saved-jobs" className={`text-white hover:text-indigo-200 ${location.pathname === '/saved-jobs' ? 'font-bold border-b-2 border-indigo-200' : ''}`}>Saved Jobs</Link></li>
            <li><Link to="/due-jobs" className={`text-white hover:text-indigo-200 ${location.pathname === '/due-jobs' ? 'font-bold border-b-2 border-indigo-200' : ''}`}>Due Jobs</Link></li>
          </ul>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-indigo-800/50 hover:bg-indigo-600 transition-all duration-200 focus:outline-none active:scale-90 border border-indigo-500/30"
            aria-label="Toggle Theme"
          >
            {theme === 'dark' ? (
              <Sun size={20} className="text-amber-400 fill-amber-400" />
            ) : (
              <Moon size={20} className="text-slate-200 fill-slate-200" />
            )}
          </button>
        </div>
      </div>
    </nav>
  );
};

const SearchBar = ({ searchTerm, setSearchTerm, filterCompany, setFilterCompany, filterTitle, setFilterTitle, handleSearch }) => {
  return (
    <div className="search-bar-container p-4 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/80 dark:border-slate-700 shadow-sm mb-8 grid grid-cols-1 md:grid-cols-4 gap-4 w-full">
      <div className="search-input-group relative">
        <input
          type="text"
          placeholder="Search by keyword..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full p-3 pl-10 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white focus:border-transparent bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 transition-colors"
        />
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
      </div>
      <div className="filter-input-group relative">
        <input
          type="text"
          placeholder="Company..."
          value={filterCompany}
          onChange={(e) => setFilterCompany(e.target.value)}
          className="w-full p-3 pl-10 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white focus:border-transparent bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 transition-colors"
        />
        <Building className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
      </div>
      <div className="filter-input-group relative">
        <input
          type="text"
          placeholder="Title..."
          value={filterTitle}
          onChange={(e) => setFilterTitle(e.target.value)}
          className="w-full p-3 pl-10 border border-slate-200 dark:border-slate-600 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:bg-white focus:border-transparent bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-50 transition-colors"
        />
        <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
      </div>
      <button 
        className="search-button bg-indigo-600 text-white font-medium p-3 rounded-xl hover:bg-indigo-700 hover:shadow-md transition-all duration-300 active:scale-95" 
        onClick={handleSearch}
      >
        Search
      </button>
    </div>
  );
};

const JobCard = ({ job }) => {
  const { savedJobIds, toggleSavedJob } = useContext(SavedJobsContext);
  const isSaved = savedJobIds.includes(job.id);

  return (
    <a
      href={job.url}
      target="_blank"
      rel="noopener noreferrer"
      className="job-card group block p-6 bg-white dark:bg-slate-800 rounded-2xl border border-slate-200/80 dark:border-slate-700 shadow-sm hover:-translate-y-1 hover:shadow-lg transition-all duration-300 ease-in-out cursor-pointer"
    >
      <div className="job-card-header flex justify-between items-start mb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors duration-200">
            {job.title}
          </h2>
          <h3 className="text-sm font-medium text-slate-600 dark:text-slate-400 mt-1">
            {job.company} • {job.location}
          </h3>
        </div>
        
        <button
          onClick={(e) => {
            e.preventDefault();
            toggleSavedJob(job.id);
          }}
          className="p-2 -mt-2 -mr-2 rounded-full hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors focus:outline-none active:scale-90"
          aria-label={isSaved ? "Remove from saved jobs" : "Save job"}
        >
          <Bookmark
            fill={isSaved ? "currentColor" : "none"}
            className={`transition-all duration-300 ${
              isSaved ? 'text-indigo-600 scale-110' : 'text-slate-400'
            }`}
            size={24}
            strokeWidth={isSaved ? 1.5 : 2}
          />
        </button>
      </div>
      
      <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed line-clamp-3">
        {job.description}
      </p>
      
      {job.isExpiringSoon && (
        <span className="urgency-badge inline-flex items-center mt-4 px-3 py-1 text-xs font-semibold rounded-full text-rose-600 bg-rose-50 border border-rose-100 dark:bg-rose-500/10 dark:text-rose-400 dark:border-rose-500/20">
          Expiring Soon!
        </span>
      )}
    </a>
  );
};

const FindJobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterCompany, setFilterCompany] = useState("");
  const [filterTitle, setFilterTitle] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [jobsPerPage] = useState(10);

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    fetch("/jobs.json")
      .then((response) => response.json())
      .then((data) => setJobs(data))
      .catch((error) => console.error("Error loading jobs:", error));
  }, []);

  useEffect(() => {
    const urlParams = new URLSearchParams(location.search);
    const company = urlParams.get("company");
    if (company) {
      setFilterCompany(company);
    }
  }, [location.search]);

  const handleSearch = () => {
    setCurrentPage(1);
  };

  const filteredJobs = jobs.filter(job => {
    return (
      job.title.toLowerCase().includes(searchTerm.toLowerCase()) &&
      job.company.toLowerCase().includes(filterCompany.toLowerCase()) &&
      job.title.toLowerCase().includes(filterTitle.toLowerCase())
    );
  });

  const indexOfLastJob = currentPage * jobsPerPage;
  const indexOfFirstJob = indexOfLastJob - jobsPerPage;
  const currentJobs = filteredJobs.slice(indexOfFirstJob, indexOfLastJob);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  return (
    <div className="main-content w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <SearchBar 
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        filterCompany={filterCompany}
        setFilterCompany={setFilterCompany}
        filterTitle={filterTitle}
        setFilterTitle={setFilterTitle}
        handleSearch={handleSearch}
      />
      <h1 className="page-title text-3xl font-bold text-slate-800 dark:text-slate-100 my-8 text-center">Find Jobs</h1>
      <div className="job-list grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 w-full max-w-7xl mx-auto">
        {currentJobs.map(job => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>
      <div className="pagination flex justify-center space-x-2 mt-8">
        {[...Array(Math.ceil(filteredJobs.length / jobsPerPage)).keys()].map(number => (
          <button key={number + 1} onClick={() => paginate(number + 1)} className={`px-4 py-2 border border-slate-300 dark:border-slate-700 rounded-md hover:bg-indigo-100 dark:hover:bg-slate-700 ${currentPage === number + 1 ? 'bg-indigo-600 text-white border-indigo-600' : ''}`}>
            {number + 1}
          </button>
        ))}
      </div>
    </div>
  );
};

const CompaniesPage = () => {
  const [companies, setCompanies] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("/jobs.json")
      .then((response) => response.json())
      .then((data) => {
        const uniqueCompanies = [...new Set(data.map(job => job.company))];
        setCompanies(uniqueCompanies);
      })
      .catch((error) => console.error("Error loading companies:", error));
  }, []);

  const handleCompanyClick = (companyName) => {
    navigate(`/find-jobs?company=${encodeURIComponent(companyName)}`);
  };

  return (
    <div className="main-content w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="page-title text-3xl font-bold text-slate-800 dark:text-slate-100 my-8 text-center">Companies</h1>
      <div className="company-grid grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {companies.map(company => (
          <div key={company} className="company-card p-6 bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm hover:-translate-y-1 hover:shadow-xl transition-all duration-300 cursor-pointer"
               onClick={() => handleCompanyClick(company)}>
            <h2 className="text-xl font-bold text-indigo-600 dark:text-indigo-400">{company}</h2>
            <p className="text-slate-600 dark:text-slate-400 mt-2">View jobs from {company}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const SavedJobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const { savedJobIds } = useContext(SavedJobsContext);

  useEffect(() => {
    fetch("/jobs.json")
      .then((response) => response.json())
      .then((data) => {
        const saved = data.filter(job => savedJobIds.includes(job.id));
        setJobs(saved);
      })
      .catch((error) => console.error("Error loading saved jobs:", error));
  }, [savedJobIds]);

  return (
    <div className="main-content w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="page-title text-3xl font-bold text-slate-800 dark:text-slate-100 my-8 text-center">Saved Jobs</h1>
      <div className="job-list grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 w-full max-w-7xl mx-auto">
        {jobs.length > 0 ? (
          jobs.map(job => <JobCard key={job.id} job={job} />)
        ) : (
          <p className="text-center text-slate-500 dark:text-slate-400 col-span-full">No saved jobs yet.</p>
        )}
      </div>
    </div>
  );
};

const DueJobsPage = () => {
  const [jobs, setJobs] = useState([]);

  useEffect(() => {
    fetch("/jobs.json")
      .then((response) => response.json())
      .then((data) => {
        const today = new Date();
        const expiringJobs = data.filter(job => {
          const postedDate = job.date_posted ? new Date(job.date_posted) : new Date();
          const deadline = new Date(postedDate);
          deadline.setDate(postedDate.getDate() + 30);

          const diffTime = deadline.getTime() - today.getTime();
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

          return diffDays > 0 && diffDays <= 3;
        }).map(job => ({ ...job, isExpiringSoon: true }));
        setJobs(expiringJobs);
      })
      .catch((error) => console.error("Error loading due jobs:", error));
  }, []);

  return (
    <div className="main-content w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="page-title text-3xl font-bold text-slate-800 dark:text-slate-100 my-8 text-center">Due Jobs</h1>
      <div className="job-list grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 w-full max-w-7xl mx-auto">
        {jobs.length > 0 ? (
          jobs.map(job => <JobCard key={job.id} job={job} />)
        ) : (
          <p className="text-center text-slate-500 dark:text-slate-400 col-span-full">No jobs expiring soon.</p>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <ThemeProvider> {/* Wrap App in ThemeProvider */}
      <SavedJobsProvider>
        <Router>
          <div className="App bg-slate-50 text-slate-950 dark:bg-slate-950 dark:text-slate-50 min-h-screen transition-colors duration-300">
            <Navbar />
            <Routes>
              <Route path="/" element={<FindJobsPage />} />
              <Route path="/find-jobs" element={<FindJobsPage />} />
              <Route path="/companies" element={<CompaniesPage />} />
              <Route path="/saved-jobs" element={<SavedJobsPage />} />
              <Route path="/due-jobs" element={<DueJobsPage />} />
            </Routes>
          </div>
        </Router>
      </SavedJobsProvider>
    </ThemeProvider>
  );
}

export default App;