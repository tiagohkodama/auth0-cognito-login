import React from 'react';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

const LoginPage = () => {
  const { login } = useAuth();

  const handleLogin = (provider) => {
    login(provider);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Welcome</h1>
        <p className="subtitle">Choose your login method</p>

        <div className="providers">
          <button
            className="provider-button cognito"
            onClick={() => handleLogin('cognito')}
          >
            <div className="provider-icon">🔐</div>
            <div className="provider-info">
              <h3>Fashion Login</h3>
              <p>Login via AWS Cognito (federated with Auth0 Fashion)</p>
            </div>
          </button>

          <button
            className="provider-button auth0"
            onClick={() => handleLogin('auth0')}
          >
            <div className="provider-icon">🔑</div>
            <div className="provider-info">
              <h3>Research Catalog Login</h3>
              <p>Login directly with Auth0 Research Catalog</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
