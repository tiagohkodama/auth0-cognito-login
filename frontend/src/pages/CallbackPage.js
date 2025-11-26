import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { setAccessToken } from '../utils/tokenManager';
import { useAuth } from '../context/AuthContext';

const CallbackPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { loadUser } = useAuth();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check if access_token is in URL (from redirect)
        const accessToken = searchParams.get('access_token');

        if (accessToken) {
          // Store token
          setAccessToken(accessToken);

          // Load user profile
          await loadUser();

          // Navigate to home
          navigate('/');
        } else {
          setError('No access token received');
          setTimeout(() => navigate('/login'), 3000);
        }
      } catch (error) {
        console.error('Callback error:', error);
        setError('Authentication failed');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [searchParams, navigate, loadUser]);

  if (error) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <h2>Authentication Error</h2>
        <p>{error}</p>
        <p>Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh'
    }}>
      <div style={{ textAlign: 'center' }}>
        <h2>Processing login...</h2>
        <p>Please wait while we authenticate you.</p>
      </div>
    </div>
  );
};

export default CallbackPage;
