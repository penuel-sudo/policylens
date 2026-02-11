import React from "react";
import { popupMock } from "./mockData";
import "./popup.css";

export const PopupApp = () => {
  return (
    <div className="pl-popup">
      <header className="pl-header">
        <div>
          <div className="pl-title">PolicyLens</div>
          <div className="pl-subtitle">Quick policy insight</div>
        </div>
        <span className="pl-pill" data-state="green">
          {popupMock.status}
        </span>
      </header>

      <section className="pl-section">
        <div className="pl-label">Last analyzed</div>
        <div className="pl-row">
          <div>
            <div className="pl-site">{popupMock.lastAnalyzed.site}</div>
            <div className="pl-meta">
              {popupMock.lastAnalyzed.policyType} · {popupMock.lastAnalyzed.updated}
            </div>
          </div>
          <span className="pl-risk" data-state="yellow">
            {popupMock.lastAnalyzed.risk}
          </span>
        </div>
      </section>

      <section className="pl-section">
        <div className="pl-label">Actions</div>
        <button className="pl-button">Analyze current page</button>
        <button className="pl-button pl-button-secondary">Open dashboard</button>
      </section>

      <section className="pl-section">
        <div className="pl-label">What happens next</div>
        <ul className="pl-list">
          {popupMock.steps.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ul>
      </section>

      <footer className="pl-footer">Local-first. AI used only when you analyze.</footer>
    </div>
  );
};
