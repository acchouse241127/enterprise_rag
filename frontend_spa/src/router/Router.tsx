import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { routes } from "./index";
import { TooltipProvider } from "@/components/ui/tooltip";

const router = createBrowserRouter(routes);

export function Router() {
  return (
    <TooltipProvider>
      <RouterProvider router={router} />
    </TooltipProvider>
  );
}
