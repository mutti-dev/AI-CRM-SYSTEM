import React, { useState } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import Sidebar2 from "./components/Sidebar2";
import Queries from "./components/EmailQueries";
import DetailsScreen from "./components/EmailDetails";
import Dashboard from "./components/Dashboard";
import Tasks from "./components/Tasks";
import Settings from "./components/Settings";
import UploadDataset from "./components/UploadDataset";
import { Routes, Route, useLocation } from "react-router-dom";
import TicketTabs from "./components/TicketTabs";
import { useParams } from "react-router-dom";
import WhatsAppMessages from "./components/WhatsAppQueries";
import WhatsAppChatDetails from "./components/WhatsAppChatDetails";
import ActionPanel from "./components/ActionPanel";

function App() {
  const { id } = useParams();
  console.log("id from APP", id);
  const location = useLocation();
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  const showActionPanelRoutes = ["/details", "/whatsapp-chat"];

  const shouldShowActionPanel = showActionPanelRoutes.some((route) =>
    location.pathname.startsWith(route)
  );

  return (
    <div className="App">
      <div className="App-container">
        {location.pathname.startsWith("/details") ? (
          <Sidebar2 onToggle={setSidebarCollapsed} emailQueryId={id} />
        ) : (
          <Sidebar onToggle={setSidebarCollapsed} emailQueryId={id} />
        )}

        <main className={`App-main ${isSidebarCollapsed ? "expanded" : ""}`}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/queries" element={<Queries />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/details/:id" element={<DetailsScreen />} />
            <Route path="/upload-dataset" element={<UploadDataset />} />
            <Route path="/whatsapp-messages" element={<WhatsAppMessages />} />
            <Route
              path="/whatsapp-chat/:chatId/:customer_name"
              element={<WhatsAppChatDetails />}
            />
          </Routes>
        </main>

        {/* 👉 Stick ActionPanel to right side if route matches */}
        {shouldShowActionPanel && (
    <div className="action-panel">
      <ActionPanel />
    </div>
  )}
      </div>
    </div>
  );
}

export default App;
