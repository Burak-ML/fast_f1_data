import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { Home } from './pages/Home';
import { Dashboard } from './pages/Dashboard';
import { Predict } from './pages/Predict';

function App() {
  return (
    <Router>
      <Navbar />
      <main className="flex-1 w-full relative">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/predict" element={<Predict />} />
        </Routes>
      </main>
      <Footer />
    </Router>
  );
}

export default App;
