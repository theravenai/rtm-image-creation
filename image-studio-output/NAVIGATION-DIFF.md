# Navigation Update — Add "Image Studio"

Edit `components/navigation.tsx`. Make three changes:

---

## 1. Add ImageIcon to imports

Find the lucide-react import block and add `ImageIcon`:

```diff
-  Globe,
+  Globe,
+  ImageIcon,
 } from "lucide-react";
```

---

## 2. Add to topBarItems (desktop horizontal bar)

Insert after the `{ href: "/library", ... }` entry:

```diff
   { href: "/library", label: "Library", icon: Library },
+  { href: "/image-studio", label: "Image Studio", icon: ImageIcon },
   { href: "/write", label: "Write", icon: PenLine },
```

---

## 3. Add to navItems (mobile bottom bar)

Insert after the `{ href: "/library", ... }` entry:

```diff
   { href: "/library", label: "Library", icon: Library },
+  { href: "/image-studio", label: "Images", icon: ImageIcon },
   { href: "/write", label: "Write", icon: PenLine },
```

Note: The mobile label is "Images" (shorter) to keep the bottom tab bar tidy.

---

That's all three changes. The `ImageIcon` import is already available in lucide-react (it's the camera/photo icon).
