// ==============================================================================
// FILE: frontend/src/lib/trpc.ts
// PURPOSE: tRPC React client declaration and type-safe RPC binding helper.
// VIVA EXPLANATION: Provides an end-to-end type-safe client hook layer for tRPC backend procedures when RPC endpoints are active.
// ==============================================================================

import { createTRPCReact } from "@trpc/react-query";
import type { AppRouter } from "../../../server/routers";

export const trpc = createTRPCReact<AppRouter>();
