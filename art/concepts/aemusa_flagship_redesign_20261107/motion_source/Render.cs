using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Runtime.InteropServices;

// 固定斜视镜头下的概念动画。沿金色纵轴建立三维坐标，逐三角面计算遮挡。
class MotionRenderer
{
    const int OutputWidth = 960, OutputHeight = 540, FrameCount = 160;
    const double AxisSlope = -0.281, OriginX = 37.0, OriginY = 693.0, CameraSin = 0.30;
    static readonly double AxisX = 1.0 / Math.Sqrt(1.0 + AxisSlope * AxisSlope);
    static readonly double AxisY = AxisSlope * AxisX;
    static readonly double CameraCos = Math.Sqrt(1.0 - CameraSin * CameraSin);
    static Texture art, plate;
    static byte[] background, pixels;
    static float[] coreDepth, depth;
    static Bitmap fullFrame, outputFrame;
    static Graphics resizer;

    static double Limit(double x, double low, double high) { return Math.Max(low, Math.Min(high, x)); }
    static byte ToByte(double x) { return (byte)Limit(x + 0.5, 0, 255); }

    class Texture
    {
        public readonly int W, H, Stride;
        public readonly byte[] Data;
        public Texture(string path)
        {
            using (Bitmap input = new Bitmap(path))
            using (Bitmap flat = new Bitmap(input.Width, input.Height, PixelFormat.Format24bppRgb))
            {
                using (Graphics g = Graphics.FromImage(flat)) g.DrawImageUnscaled(input, 0, 0);
                W = flat.Width; H = flat.Height;
                BitmapData buf = flat.LockBits(new Rectangle(0, 0, W, H), ImageLockMode.ReadOnly, PixelFormat.Format24bppRgb);
                Stride = buf.Stride; Data = new byte[Stride * H];
                Marshal.Copy(buf.Scan0, Data, 0, Data.Length);
                flat.UnlockBits(buf);
            }
        }
    }

    // 分段单调三次插值让描出的外缘连续，并且不会在尖端过冲。
    class Profile
    {
        public readonly double[] X;
        readonly double[][] value, slope;
        public Profile(double[,] knots)
        {
            int n = knots.GetLength(0), channels = knots.GetLength(1) - 1;
            X = new double[n]; value = new double[channels][]; slope = new double[channels][];
            for (int i = 0; i < n; i++) X[i] = knots[i, 0];
            for (int c = 0; c < channels; c++)
            {
                value[c] = new double[n]; slope[c] = new double[n];
                double[] sec = new double[n - 1];
                for (int i = 0; i < n; i++) value[c][i] = knots[i, c + 1];
                for (int i = 0; i < n - 1; i++) sec[i] = (value[c][i+1] - value[c][i]) / (X[i+1] - X[i]);
                slope[c][0] = sec[0]; slope[c][n - 1] = sec[n - 2];
                for (int i = 1; i < n - 1; i++)
                {
                    double l = sec[i - 1], r = sec[i];
                    if (l * r <= 0) continue;
                    double d0 = X[i] - X[i-1], d1 = X[i+1] - X[i];
                    double a = 2*d1 + d0, b = d1 + 2*d0;
                    slope[c][i] = (a + b) / (a/l + b/r);
                }
            }
        }
        public double Start { get { return X[0]; } }
        public double End { get { return X[X.Length-1]; } }
        public double At(double x, int c)
        {
            if (x <= Start) return value[c][0];
            if (x >= End) return value[c][X.Length - 1];
            int i = Array.BinarySearch(X, x);
            if (i >= 0) return value[c][i];
            i = ~i - 1;
            double h = X[i+1] - X[i], t = (x-X[i])/h, q = 1.0-t;
            return (1+2*t)*q*q*value[c][i] + t*q*q*h*slope[c][i]
                 + t*t*(3-2*t)*value[c][i+1] - t*t*q*h*slope[c][i+1];
        }
    }

    struct V3
    {
        public double L, B, C;
        public V3(double l, double b, double c) { L=l; B=b; C=c; }
        public static V3 operator -(V3 a, V3 b) { return new V3(a.L-b.L,a.B-b.B,a.C-b.C); }
        public static V3 Normal(V3 u, V3 v)
        {
            double l=u.B*v.C-u.C*v.B, b=u.C*v.L-u.L*v.C, c=u.L*v.B-u.B*v.L;
            double d=Math.Sqrt(l*l+b*b+c*c);
            return d<1e-9 ? new V3(0,0,0) : new V3(l/d,b/d,c/d);
        }
    }
    struct Vertex
    {
        public V3 Pos;
        public double U, VFront, VBack, BackFinish;
    }
    struct Face
    {
        public int A,B,C;
        public bool Inner;
        public V3 Normal;
    }
    struct Projected
    {
        public double X,Y,Depth;
    }
    class Shell
    {
        public Profile Outline;
        public Vertex[] Vertices;
        public Projected[] Projected;
        public Face[] Faces;
        public Shell(double[,] stations, double depthStart, double depthEnd, double depthArc)
        {
            Outline = new Profile(stations);
            List<Vertex> vs = new List<Vertex>();
            List<Face> fs = new List<Face>();
            List<double> xs = new List<double>();
            for (int n=0;n<Outline.X.Length-1;n++)
            {
                double a=Outline.X[n], b=Outline.X[n+1];
                int count=(int)Math.Ceiling((b-a)/12.0);
                for(int k=0;k<count;k++) xs.Add(a+(b-a)*k/count);
            }
            xs.Add(Outline.End);
            foreach(double x in xs)
            {
                double t=(x-Outline.Start)/(Outline.End-Outline.Start);
                double top=Outline.At(x,0), bottom=Math.Max(top,Outline.At(x,2));
                double ridge=Limit(Outline.At(x,1),top,bottom);
                double w=bottom-top;
                double c0=depthStart+(depthEnd-depthStart)*t+depthArc*Math.Sin(Math.PI*t);
                double[] ys={top, top+.48*(ridge-top), ridge, ridge+.53*(bottom-ridge), bottom,
                             bottom-.28*w, top+.44*w, top+.12*w};
                double[] cc={0,.13,.21,.13,0,-.17,-.254,-.145};
                double[] reverseUV={.045,.18,.42,.72,.94,.72,.45,.16};
                double[] backFinish={.90,.90,.90,.90,.29,.55,.93,.99};
                for(int row=0;row<ys.Length;row++)
                {
                    double y=ys[row], c=c0+w*cc[row];
                    double u=(x-OriginX)*AxisX+(y-OriginY)*AxisY;
                    double b=-(x-OriginX)*AxisY+(y-OriginY)*AxisX;
                    double inset=Math.Min(1.15,w*.12);
                    vs.Add(new Vertex { Pos=new V3((u-CameraSin*c)/CameraCos,b,c), U=x,
                                        VFront=Limit(y,top+inset,bottom-inset),
                                        VBack=top+(ridge-top)*reverseUV[row], BackFinish=backFinish[row] });
                }
            }
            Vertices=vs.ToArray(); Projected=new Projected[Vertices.Length];
            for(int i=0;i<xs.Count-1;i++) for(int row=0;row<8;row++)
            {
                int next=(row+1)%8, a=i*8+row, b=(i+1)*8+row, c=(i+1)*8+next, d=i*8+next;
                AddFace(fs,a,b,c,row>=4); AddFace(fs,a,c,d,row>=4);
            }
            Faces=fs.ToArray();
        }
        void AddFace(List<Face> fs,int a,int b,int c,bool inner)
        {
            V3 n=V3.Normal(Vertices[b].Pos-Vertices[a].Pos,Vertices[c].Pos-Vertices[a].Pos);
            fs.Add(new Face {A=a,B=b,C=c,Inner=inner,Normal=n});
        }
    }

    static Shell[] BuildShells()
    {
        // 每截记录左图坐标 x、银面上缘、折线和厚侧壁下缘。
        return new Shell[] {
            new Shell(new double[,] {
                {96,660,660,660},{125,641.5,648.4,651},{150,625.5,640,644},{175,611,626.5,632},
                {250,565,584,597},{350,503,534.6,551},{450,444,490,502},{500,418,471.3,484},
                {650,350.1,415.7,432.7},{750,317.5,384,403},{800,307.8,369.7,389},
                {850,304.0,357.6,376},{900,306.2,346.2,364},{930,312.6,339.4,357.5},
                {950,317.7,335.9,353.7},{970,325,332.8,345.9},{982.5,330.0,330.0,330.0}}, 16,74,18),
            new Shell(new double[,] {
                {170,699.3,699.3,699.3},{220,685.7,693.3,697.0},{250,678.8,689.1,695.8},
                {350,653.3,676.2,690.9},{500,610.5,652.2,680},{650,566.6,625.0,663.4},
                {750,538.7,603.1,649.5},{800,524.1,591,641.0},{850,509.9,577.4,630.3},
                {900,495.9,561.2,617.2},{950,482.6,541.8,596.7},{990,471.6,523.0,576},
                {1020,463.8,508.8,554},{1050,456.6,492.5,527},{1080,449.6,474.3,497},
                {1100,444.6,460.5,473.5},{1128,438.1,438.1,438.1}}, 28,93,37),
            new Shell(new double[,] {
                {982.7,288.1,288.1,288.1},{990,275.6,282.5,286.8},{1020,235.2,260.1,283.8},
                {1050,210.1,245.7,280.8},{1100,184.3,224.2,275.5},{1149,165.9,205.0,271.0},
                {1175,157,196.7,258},{1200,150.7,189.4,245.2},{1250,140.4,174.6,223.7},
                {1300,132.3,162.8,210.3},{1350,128.3,154.3,197.2},{1380,127.2,150.8,190.3},
                {1400,127.1,149.1,185.8},{1450,130.6,147.9,177.5},{1490,135.5,148.6,172.4},
                {1550,147.2,154.6,165.3},{1578,155.7,160.2,165.6},{1613.2,169.6,169.6,169.6}}, 50,25,14),
            new Shell(new double[,] {
                {1145.8,429.5,429.5,429.5},{1160,419.5,424.4,427.6},{1200,402.3,415.1,423.5},
                {1250,385.5,405.6,421.5},{1300,368.7,397.9,419.5},{1350,351.6,390.1,415.5},
                {1380,340.6,382.8,408.9},{1400,333.8,375.4,400.8},{1450,316.7,343.3,371.0},
                {1470,310.0,324.9,342.7},{1487.8,304.0,304.0,304.0}}, 109,76,19)
        };
    }

    static double Fade(double t)
    {
        t=Limit(t,0,1); return t*t*(3-2*t);
    }
    static void PrepareBackdrop()
    {
        Profile hull = new Profile(new double[,] {
            {37,693,693},{74,669.3,687.3},{100,656.8,685},{125,648.8,681.9},{150,640.0,678.4},
            {175,630,675},{250,599.6,665},{350,559.9,651},{500,502.2,630.4},{650,444.2,607.9},
            {800,386.9,583.0},{900,349.4,564.0},{982,318.1,547.0},{1050,294.7,530.6},
            {1100,281.2,518.1},{1150,270.2,500.2},{1200,261.1,482.2},{1300,245.8,440.8},
            {1380,237.0,403.2},{1450,231.5,364.8},{1490,229.9,340.7},{1550,230.1,298.7},
            {1580,232.8,273.4},{1603.5,244.4,246.5},{1605,245.3,245.3} });
        background=(byte[])plate.Data.Clone(); coreDepth=new float[art.W*art.H];
        for(int x=0;x<art.W;x++)
        {
            double h0=hull.At(x,0),h1=hull.At(x,1),half=(h1-h0)/2,mid=(h0+h1)/2;
            for(int y=0;y<art.H;y++)
            {
                // 使用统一补画的天空，消除银壳挪开后旧位置周围的亮边。
                // 中央星系与轴线的细节直接取自所选第二稿。
                double along=(x-1101)*AxisX+(y-364)*AxisY, across=-(x-1101)*AxisY+(y-364)*AxisX;
                double galaxy=Fade((1-Math.Sqrt(along*along/(164*164)+across*across/(60*60)))/.28);
                double goldY=x<846 ? 692.0-.289*(x-37) : 458.2-.246*(x-846);
                double gold=Fade((29-Math.Abs(y-goldY))/12)*Fade((x-225)/100.0)*Fade((1270-x)/65.0);
                double opacity=Math.Max(galaxy,gold);
                if(opacity>0)
                {
                    int idx=y*art.Stride+x*3;
                    for(int c=0;c<3;c++) background[idx+c]=ToByte(art.Data[idx+c]*opacity+plate.Data[idx+c]*(1-opacity));
                }
                float z=-100000;
                if(x>=hull.Start && x<=hull.End && half>0 && y>h0 && y<h1)
                {
                    double f=(y-mid)/half;
                    z=(float)(.65*half*Math.Sqrt(Math.Max(0,1-f*f)));
                }
                coreDepth[y*art.W+x]=z;
            }
        }
        pixels=new byte[background.Length]; depth=new float[coreDepth.Length];
    }

    static double Illum(double l,double b,double c)
    {
        return Math.Max(0,-.267*l-.638*b+.723*c);
    }
    static void DrawShell(Shell shell,double cs,double sn)
    {
        for(int i=0;i<shell.Vertices.Length;i++)
        {
            V3 p=shell.Vertices[i].Pos;
            double b=p.B*cs-p.C*sn,c=p.B*sn+p.C*cs,u=CameraCos*p.L+CameraSin*c;
            shell.Projected[i]=new Projected {X=OriginX+AxisX*u-AxisY*b,Y=OriginY+AxisY*u+AxisX*b,Depth=c};
        }
        foreach(Face f in shell.Faces)
        {
            V3 n=f.Normal;
            double nb=n.B*cs-n.C*sn,nc=n.B*sn+n.C*cs,view=CameraCos*nc-CameraSin*n.L;
            if(view<.00001) continue;
            double lit=Illum(n.L,nb,nc);
            double r,g,b,add;
            if(f.Inner)
            {
                double rim=.09*Math.Pow(1-Limit(view,0,1),3);
                r=.46+.43*lit+rim; g=.50+.42*lit+rim; b=.61+.32*lit+rim; add=3;
            }
            else
            {
                double baseLight=Illum(n.L,n.B,n.C);
                double gain=Limit((.61+.39*lit)/(.61+.39*baseLight),.62,1.30);
                r=gain; g=.03+.97*gain; b=.09+.91*gain; add=0;
            }
            DrawFace(shell,f,r,g,b,add);
        }
    }

    static void DrawFace(Shell s,Face f,double red,double green,double blue,double add)
    {
        Projected a=s.Projected[f.A], b=s.Projected[f.B], c=s.Projected[f.C];
        double x1=b.X-a.X, x2=c.X-a.X, y1=b.Y-a.Y, y2=c.Y-a.Y;
        double area=x1*y2-x2*y1;
        if(Math.Abs(area)<.00001) return;
        int xMin=Math.Max(0,(int)Math.Floor(Math.Min(a.X,Math.Min(b.X,c.X))));
        int xMax=Math.Min(art.W-1,(int)Math.Ceiling(Math.Max(a.X,Math.Max(b.X,c.X))));
        int yMin=Math.Max(0,(int)Math.Floor(Math.Min(a.Y,Math.Min(b.Y,c.Y))));
        int yMax=Math.Min(art.H-1,(int)Math.Ceiling(Math.Max(a.Y,Math.Max(b.Y,c.Y))));
        double ix1=y2/area, iy1=-x2/area, ix2=-y1/area, iy2=x1/area;
        Vertex va=s.Vertices[f.A], vb=s.Vertices[f.B], vc=s.Vertices[f.C];
        double v0=f.Inner?va.VBack:va.VFront,v1=(f.Inner?vb.VBack:vb.VFront)-v0,v2=(f.Inner?vc.VBack:vc.VFront)-v0;
        double u1=vb.U-va.U,u2=vc.U-va.U,d1=b.Depth-a.Depth,d2=c.Depth-a.Depth;
        for(int y=yMin;y<=yMax;y++)
        {
            double w1=(xMin-a.X)*ix1+(y-a.Y)*iy1, w2=(xMin-a.X)*ix2+(y-a.Y)*iy2;
            int zi=y*art.W+xMin, pi=y*art.Stride+xMin*3;
            for(int x=xMin;x<=xMax;x++,w1+=ix1,w2+=ix2,zi++,pi+=3)
            {
                if(w1<-.00001||w2<-.00001||w1+w2>1.00001) continue;
                double z=a.Depth+w1*d1+w2*d2;
                if(z<depth[zi]) continue;
                double u=va.U+w1*u1+w2*u2, v=v0+w1*v1+w2*v2;
                int tx=(int)u, ty=(int)v, offset=ty*art.Stride+tx*3;
                double fu=u-tx, fv=v-ty;
                double w00=(1-fu)*(1-fv), w10=fu*(1-fv), w01=(1-fu)*fv, w11=fu*fv;
                double finish=f.Inner ? va.BackFinish+w1*(vb.BackFinish-va.BackFinish)+w2*(vc.BackFinish-va.BackFinish) : 1;
                for(int ch=0;ch<3;ch++)
                {
                    int q=offset+ch;
                    double col=art.Data[q]*w00+art.Data[q+3]*w10+art.Data[q+art.Stride]*w01+art.Data[q+art.Stride+3]*w11;
                    double gain=ch==0?blue:(ch==1?green:red);
                    double lining=ch==0?83:(ch==1?48:35);
                    pixels[pi+ch]=ToByte(lining+(col*gain+add-lining)*finish);
                }
                depth[zi]=(float)z;
            }
        }
    }

    static void SaveFrame(string path)
    {
        BitmapData bits=fullFrame.LockBits(new Rectangle(0,0,art.W,art.H),ImageLockMode.WriteOnly,PixelFormat.Format24bppRgb);
        Marshal.Copy(pixels,0,bits.Scan0,pixels.Length); fullFrame.UnlockBits(bits);
        resizer.DrawImage(fullFrame,new Rectangle(0,0,OutputWidth,OutputHeight),0,0,art.W,art.H,GraphicsUnit.Pixel);
        outputFrame.Save(path,ImageFormat.Png);
    }

    static int Main(string[] args)
    {
        if(args.Length<3) return 2;
        art=new Texture(args[0]); plate=new Texture(args[1]);
        if(art.W!=1672||art.H!=941||art.W!=plate.W||art.H!=plate.H) throw new InvalidDataException("图层尺寸不匹配");
        string folder=args[2]; Directory.CreateDirectory(folder); bool proof=args.Length>3 && args[3]=="proof";
        Shell[] shells=BuildShells(); PrepareBackdrop();
        using(fullFrame=new Bitmap(art.W,art.H,PixelFormat.Format24bppRgb))
        using(outputFrame=new Bitmap(OutputWidth,OutputHeight,PixelFormat.Format24bppRgb))
        using(resizer=Graphics.FromImage(outputFrame))
        {
            resizer.InterpolationMode=InterpolationMode.HighQualityBicubic;
            resizer.PixelOffsetMode=PixelOffsetMode.HighQuality;
            resizer.CompositingMode=CompositingMode.SourceCopy;
            for(int i=0;i<FrameCount;i++)
            {
                if(proof && i%20!=0) continue;
                Buffer.BlockCopy(background,0,pixels,0,pixels.Length);
                Buffer.BlockCopy(coreDepth,0,depth,0,depth.Length*sizeof(float));
                double theta=i*2*Math.PI/FrameCount;
                foreach(Shell s in shells) DrawShell(s,Math.Cos(theta),Math.Sin(theta));
                SaveFrame(Path.Combine(folder,i.ToString("D3",CultureInfo.InvariantCulture)+".png"));
            }
        }
        Console.WriteLine(proof?"8 views":"160 frames, 960x540"); return 0;
    }
}
