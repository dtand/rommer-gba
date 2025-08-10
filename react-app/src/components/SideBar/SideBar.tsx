import React from 'react';

const SideBar: React.FC = () => (
  <aside style={{ width: '220px', background: '#f8f9fa', height: '100vh', padding: '24px 12px', boxSizing: 'border-box', borderRight: '1px solid #ddd' }}>
    <h2 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Menu</h2>
    <ul style={{ listStyle: 'none', padding: 0 }}>
      <li><a href="#sessions">Sessions</a></li>
      <li><a href="#annotations">Annotations</a></li>
      <li><a href="#settings">Settings</a></li>
    </ul>
  </aside>
);

export default SideBar;
