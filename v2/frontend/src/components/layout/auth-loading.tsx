import { Skeleton } from "@/components/ui/skeleton";

export function AuthLoading() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar skeleton */}
      <div className="hidden w-64 border-r p-4 md:block">
        <Skeleton className="mb-6 h-8 w-32" />
        <Skeleton className="mb-4 h-10 w-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
        <div className="mt-6 space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      </div>
      {/* Main content skeleton */}
      <div className="flex flex-1 flex-col">
        {/* Header skeleton */}
        <div className="flex h-16 items-center border-b px-4">
          <Skeleton className="h-8 w-8 rounded-md" />
          <Skeleton className="ml-4 h-6 w-32" />
          <div className="flex-1" />
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="ml-2 h-8 w-8 rounded-full" />
        </div>
        {/* Content area skeleton */}
        <div className="flex-1 p-6">
          <Skeleton className="mb-2 h-8 w-48" />
          <Skeleton className="mb-6 h-4 w-72" />
          <div className="space-y-4">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
