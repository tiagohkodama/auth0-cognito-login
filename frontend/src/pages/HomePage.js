import React from 'react';
import { useAuth } from '../context/AuthContext';
import './HomePage.css';

const HomePage = () => {
  const { user, logout } = useAuth();

  return (
    <div className="home-container">
      <div className="home-card">
        <h1>Welcome Back!</h1>

        {user && (
          <div className="user-info">
            <div className="info-row">
              <span className="label">Email:</span>
              <span className="value">{user.email}</span>
            </div>

            <div className="info-row">
              <span className="label">Primary Provider:</span>
              <span className="value">{user.primary_provider}</span>
            </div>

            <div className="info-row">
              <span className="label">Email Verified:</span>
              <span className="value">{user.email_verified ? 'Yes' : 'No'}</span>
            </div>

            {user.last_login_at && (
              <div className="info-row">
                <span className="label">Last Login:</span>
                <span className="value">
                  {new Date(user.last_login_at).toLocaleString()}
                </span>
              </div>
            )}

            {user.linked_identities && user.linked_identities.length > 0 && (
              <div className="linked-section">
                <h3>Linked Accounts</h3>
                {user.linked_identities.map((identity, index) => (
                  <div key={index} className="linked-identity">
                    <span>{identity.provider}</span>
                    <span className="linked-email">{identity.email}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <button className="logout-button" onClick={logout}>
          Logout
        </button>
      </div>
    </div>
  );
};

export default HomePage;
