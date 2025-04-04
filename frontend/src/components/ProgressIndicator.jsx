import * as Progress from '@radix-ui/react-progress';

export default function ProgressIndicator({ progress }) {
  return (
    <div className="flex items-center gap-2">
      <Progress.Root
        className="relative h-3 w-24 overflow-hidden rounded-full bg-gray-200"
        style={{
          // Fix overflow clipping in Safari
          transform: 'translateZ(0)',
        }}
        value={progress}
      >
        <Progress.Indicator
          className="h-full w-full flex-1 bg-blue-500 transition-transform duration-500 ease-[cubic-bezier(0.65,0,0.35,1)]"
          style={{ transform: `translateX(-${100 - progress}%)` }}
        />
      </Progress.Root>
      <span className="text-sm text-gray-600">{progress}%</span>
    </div>
  );
} 