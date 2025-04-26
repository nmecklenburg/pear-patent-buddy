import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="w-full max-w-2xl shadow-lg">
        <CardHeader className="space-y-2">
          <CardTitle className="text-2xl font-bold text-primary">Patent Search Assistant</CardTitle>
          <CardDescription className="text-muted-foreground">
            Describe your invention and we'll help you find relevant prior art
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="space-y-2">
              <label
                htmlFor="description"
                className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
              >
                Invention Description
              </label>
              <Textarea
                id="description"
                placeholder="Enter a detailed description of your invention..."
                className="min-h-[150px] resize-none"
              />
            </div>
            <Button className="w-full sm:w-auto" size="lg">
              Search Prior Art
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
