import React, { useState } from 'react';
import { Container, Tab, Tabs } from 'react-bootstrap';
import LiveScores from '../components/LiveScores';
import PredictionsView from '../components/PredictionsView';
import ValueBets from '../components/ValueBets';
import SquadView from '../components/SquadView';
import { Activity, Brain, DollarSign, Users } from 'lucide-react';
import 'bootstrap/dist/css/bootstrap.min.css';
import './SportMonks.css';

const SportMonks: React.FC = () => {
  const [activeTab, setActiveTab] = useState('live');

  return (
    <Container fluid className="sportmonks-container py-4">
      <div className="sportmonks-header mb-4">
        <h1 className="display-4 mb-2">SportMonks Football Intelligence</h1>
        <p className="lead text-muted">
          Real-time scores, AI predictions, and value betting opportunities powered by SportMonks API
        </p>
      </div>

      <Tabs
        activeKey={activeTab}
        onSelect={(k) => setActiveTab(k || 'live')}
        className="sportmonks-tabs mb-4"
      >
        <Tab 
          eventKey="live" 
          title={
            <span className="tab-title">
              <Activity size={20} className="me-2" />
              Live Scores
            </span>
          }
        >
          <div className="tab-content-wrapper">
            <LiveScores />
          </div>
        </Tab>
        
        <Tab 
          eventKey="predictions" 
          title={
            <span className="tab-title">
              <Brain size={20} className="me-2" />
              AI Predictions
            </span>
          }
        >
          <div className="tab-content-wrapper">
            <PredictionsView />
          </div>
        </Tab>
        
        <Tab 
          eventKey="valuebets" 
          title={
            <span className="tab-title">
              <DollarSign size={20} className="me-2" />
              Value Bets
            </span>
          }
        >
          <div className="tab-content-wrapper">
            <ValueBets />
          </div>
        </Tab>
        
        <Tab 
          eventKey="squads" 
          title={
            <span className="tab-title">
              <Users size={20} className="me-2" />
              Team Squads
            </span>
          }
        >
          <div className="tab-content-wrapper">
            <SquadView />
          </div>
        </Tab>
      </Tabs>
    </Container>
  );
};

export default SportMonks;