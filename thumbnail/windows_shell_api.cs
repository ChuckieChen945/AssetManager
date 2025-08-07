
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public class ThumbnailExtractor
{
    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    public static extern void SHCreateItemFromParsingName(
        [In][MarshalAs(UnmanagedType.LPWStr)] string pszPath,
        [In] IntPtr pbc,
        [In][MarshalAs(UnmanagedType.LPStruct)] Guid riid,
        [Out][MarshalAs(UnmanagedType.Interface, IidParameterIndex = 2)] out IShellItem ppv
    );

    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("43826d1e-e718-42ee-bc55-a1e261c37bfe")]
    public interface IShellItem
    {
        void BindToHandler();
        void GetParent();
        void GetDisplayName();
        void GetAttributes();
        void Compare();
    }

    [ComImport]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    [Guid("bcc18b79-ba16-442f-80c4-8a59c30c463b")]
    public interface IShellItemImageFactory
    {
        void GetImage(
            [In] SIZE size,
            [In] int flags,
            [Out] out IntPtr phbm
        );
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct SIZE
    {
        public int cx;
        public int cy;
    }

    private static Bitmap GetBitmapFromHBitmap(IntPtr nativeHBitmap)
    {
        Bitmap bmp = Bitmap.FromHbitmap(nativeHBitmap);

        if (Bitmap.GetPixelFormatSize(bmp.PixelFormat) < 32)
            return bmp;

        BitmapData bmpData;

        if (IsAlphaBitmap(bmp, out bmpData))
            return GetlAlphaBitmapFromBitmapData(bmpData);

        return bmp;
    }

    private static Bitmap GetlAlphaBitmapFromBitmapData(BitmapData bmpData)
    {
        return new Bitmap(
                bmpData.Width,
                bmpData.Height,
                bmpData.Stride,
                PixelFormat.Format32bppArgb,
                bmpData.Scan0);
    }

    private static bool IsAlphaBitmap(Bitmap bmp, out BitmapData bmpData)
    {
        Rectangle bmBounds = new Rectangle(0, 0, bmp.Width, bmp.Height);

        bmpData = bmp.LockBits(bmBounds, ImageLockMode.ReadOnly, bmp.PixelFormat);

        try
        {
            for (int y = 0; y <= bmpData.Height - 1; y++)
            {
                for (int x = 0; x <= bmpData.Width - 1; x++)
                {
                    Color pixelColor = Color.FromArgb(
                        Marshal.ReadInt32(bmpData.Scan0, (bmpData.Stride * y) + (4 * x)));

                    if (pixelColor.A > 0 & pixelColor.A < 255)
                    {
                        return true;
                    }
                }
            }
        }
        finally
        {
            bmp.UnlockBits(bmpData);
        }

        return false;
    }


    public static Bitmap GetThumbnail(string filePath, int size)
    {
        try
        {
            IShellItem shellItem;
            Guid shellItemGuid = new Guid("43826d1e-e718-42ee-bc55-a1e261c37bfe");
            SHCreateItemFromParsingName(filePath, IntPtr.Zero, shellItemGuid, out shellItem);

            IShellItemImageFactory imageFactory = (IShellItemImageFactory)shellItem;
            SIZE thumbnailSize = new SIZE { cx = size, cy = size };
            IntPtr hBitmap;
            imageFactory.GetImage(thumbnailSize, 0, out hBitmap);

            return GetBitmapFromHBitmap(hBitmap);
        }
        catch
        {
            return null;
        }
    }
}