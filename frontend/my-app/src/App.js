import logo from './logo.svg';
import './App.css';
import React from 'react';
import CommentsSection from './components/CommentsSection';
import TopicsSection from './components/TopicsSection';

function App() {
  return (
    <div className="main-container">
      <div className="container">
        <TopicsSection />
      </div>
      <div className="list-container">
        <CommentsSection />
      </div>
    </div>
  );
}

export default App;
