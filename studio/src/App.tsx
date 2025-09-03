
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './contexts/ThemeContext';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Simulator from './pages/Simulator';
import Procedures from './pages/Procedures';
import ProcedureEditor from './pages/ProcedureEditor';
import Automations from './pages/Automations';
import AutomationEditor from './pages/AutomationEditor';
import Intake from './pages/Intake';
import Leads from './pages/Leads';
import RAG from './pages/RAG';

// Criar QueryClient para React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutos
      retry: 1,
    },
  },
});

// Placeholder components para rotas ainda não implementadas
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="text-center py-12">
    <h1 className="text-3xl font-bold text-gray-900 mb-4">{title}</h1>
    <p className="text-gray-600">Esta página está sendo implementada...</p>
    <div className="mt-8">
      <div className="inline-flex items-center px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg">
        🚧 Em desenvolvimento
      </div>
    </div>
  </div>
);

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <Router>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="simulator" element={<Simulator />} />
              <Route path="procedures" element={<Procedures />} />
              <Route path="procedures/new" element={<ProcedureEditor />} />
              <Route path="procedures/:id/edit" element={<ProcedureEditor />} />
              <Route path="automations" element={<Automations />} />
              <Route path="automations/new" element={<AutomationEditor />} />
              <Route path="automations/:id/edit" element={<AutomationEditor />} />
              <Route path="intake" element={<Intake />} />
              <Route path="leads" element={<Leads />} />
              <Route path="rag" element={<RAG />} />
              <Route path="publish" element={<PlaceholderPage title="Publicação" />} />
              <Route path="*" element={
                <div className="text-center py-12">
                  <h1 className="text-3xl font-bold text-gray-900 mb-4">Página não encontrada</h1>
                  <p className="text-gray-600">A página que você procura não existe.</p>
                </div>
              } />
            </Route>
          </Routes>
        </Router>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;