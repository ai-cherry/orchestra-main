import * as AspectRatioPrimitive from "@radix-ui/react-aspect-ratio"

function AspectRatio({
  ...props
}) {
  return <AspectRatioPrimitive.t data-slot="aspect-ratio" {...props} />;
}

export { AspectRatio }
