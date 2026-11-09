import { relayer } from "../../lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  return relayer("/kb/stats");
}
