<template>
  <div id="app-root">
    <header class="app-header">
      <router-link to="/" class="logo">AgAutoEval</router-link>
      <nav>
        <router-link to="/">Runs</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style>
#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
.app-header {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 0 24px;
  height: 52px;
  background: #161b22;
  border-bottom: 1px solid #30363d;
  flex-shrink: 0;
}
.app-header .logo {
  font-size: 16px;
  font-weight: 700;
  color: #58a6ff;
  text-decoration: none;
}
.app-header nav a {
  color: #8b949e;
  text-decoration: none;
  font-size: 14px;
}
.app-header nav a:hover,
.app-header nav a.router-link-exact-active {
  color: #e1e4e8;
}
.app-main {
  flex: 1;
  padding: 24px;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
}

/* shared table styles */
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
th {
  text-align: left;
  padding: 10px 12px;
  color: #8b949e;
  font-weight: 600;
  border-bottom: 1px solid #30363d;
  white-space: nowrap;
}
td {
  padding: 8px 12px;
  border-bottom: 1px solid #21262d;
  vertical-align: top;
}
tr:hover td {
  background: #161b22;
}

/* shared card */
.card {
  background: #161b22;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

/* shared badges */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
.badge-green { background: #1b3826; color: #3fb950; }
.badge-red  { background: #3d1f1f; color: #f85149; }
.badge-gray { background: #21262d; color: #8b949e; }
.badge-blue { background: #1a2d4a; color: #58a6ff; }

.link {
  color: #58a6ff;
  text-decoration: none;
}
.link:hover { text-decoration: underline; }

.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 12px;
}

h2 {
  font-size: 18px;
  margin-bottom: 16px;
  font-weight: 600;
}
h3 {
  font-size: 15px;
  margin-bottom: 12px;
  font-weight: 600;
}
</style>
