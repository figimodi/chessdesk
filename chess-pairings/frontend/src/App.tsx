import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Router } from "@/router/Router";

function App() {
  return (
    <>
      <Router />
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  );
}

export default App;
