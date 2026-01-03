import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    business_name: '',
    loan_amount: ''
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    // Use VITE_API_URL from environment or default to localhost
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

    try {
      const response = await axios.post(`${apiUrl}/form`, {
        ...formData,
        loan_amount: Number(formData.loan_amount)
      });
      setMessage(`Success! Submission ID: ${response.data.id}`);
      setFormData({ name: '', email: '', business_name: '', loan_amount: '' });
    } catch (error) {
      console.error('Submission error:', error);
      setMessage('Error submitting form. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Lender Matching Application</h1>
      <form onSubmit={handleSubmit} className="submission-form">
        <div className="form-group">
          <label>Name:</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Business Name:</label>
          <input
            type="text"
            name="business_name"
            value={formData.business_name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Loan Amount ($):</label>
          <input
            type="number"
            name="loan_amount"
            value={formData.loan_amount}
            onChange={handleChange}
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Application'}
        </button>
      </form>
      {message && <p className="message">{message}</p>}
    </div>
  );
}

export default App;
