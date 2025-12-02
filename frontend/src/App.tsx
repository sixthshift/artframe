import { Route, Switch, Router, useLocation } from 'wouter-preact'
import { Layout } from './components/Layout'
import { Dashboard, Plugins, Schedule, System, Config } from './pages'

const Routes = () => {
  // Subscribe to location changes to trigger re-renders
  useLocation()

  return (
    <Router>
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/plugins" component={Plugins} />
      <Route path="/schedule" component={Schedule} />
      <Route path="/system" component={System} />
      <Route path="/config" component={Config} />
      <Route>
        <div class="card">
          <h2>404 - Not Found</h2>
          <p>The page you're looking for doesn't exist.</p>
        </div>
      </Route>
    </Switch>
    </Router>
  )
}

export const App = () => {
  return (
    <Layout>
      <Routes />
    </Layout>
  )
}

