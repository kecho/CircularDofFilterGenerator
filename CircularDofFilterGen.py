#!/usr/bin/python
import argparse
import math

""" 
    ********************************************************************
    ********************************************************************
    *         Generated Filter by CircularDofFilterGenerator tool      *
    *     Copyright (c)     Kleber A Garcia  (kecho_garcia@hotmail.com)*
    *         https://github.com/kecho/CircularDofFilterGenerator      *
    ********************************************************************
    ********************************************************************
    **")
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE. 
"""

def generateFilter(lan, r, c):
    P = []
    ##             a         b         A           B
    a = 0
    b = 1
    A = 2
    B = 3
    if c == 1:
        P = [[ 1.624835, -0.862325, 0.767583, 1.862321 ]]
    elif c == 2:
        P = [
         [ 5.268909, -0.886528,  0.411259, -0.548794 ],
         [ 1.558213, -1.960518,  0.513282, 4.561110  ]]
    elif c == 3:
        P = [
         [ 5.043495, -2.176490, 1.621035, -2.105439  ],
         [ 9.027613, -1.019306, -0.280860, -0.162882 ],
         [ 1.597273, -2.815110, -0.366471, 10.300301 ]]
    elif c == 4:
        P = [
         [ 1.553635, -4.338459, -5.767909, 46.164397],
         [ 4.693183, -3.839993, 9.795391, 15.227561 ],
         [ 8.178137, -2.791880, -3.048324, 0.302959 ],
         [ 12.328289, -1.342190, 0.010001, 0.244650 ]]
    elif c == 5:
        P = [
         [ 1.685979, -4.892608, -22.356787, 85.912460  ],
         [ 4.998496, -4.711870, 35.918936 , -28.875618 ],
         [ 8.244168, -4.052795, -13.212253, -1.578428  ],
         [ 11.900859, -2.929212,  0.507991, 1.816328   ],
         [ 16.116382, -1.512961, 0.138051, -0.010000   ]]
    else:
        print("Invalid component count. Must be [1-5].");
        return;

    def KernelFun(x, C):
        return (
            math.cos(x*x*C[a]) * math.exp( x * x * C[b]), #real
            math.sin(x*x*C[a]) * math.exp( x * x * C[b]), #imaginary
            C[A], #real weight
            C[B]  #imaginary weight
        ) 

    kernels = [[KernelFun(float(i)/float(r), C) for i in range(-r,r+1,1)] for C in P]

    #normalize kernels
    accum = 0.0
    for k in kernels:
        for v in k:
            for w in k:
                accum = accum + v[A]*(v[0]*w[0] - v[1]*w[1]) +  v[B]*(v[0]*w[1] + v[1]*w[0])

    normConstant = 1.0 / math.sqrt(accum)
    kernelsNormalized = [[ (normConstant*real, normConstant*im, 0.0, 0.0) for (real, im, Av, Bv) in k  ] for  k in kernels]

    #bracket the kernel so we maximize precision. This means figureout a Offset and a Scale
    #            real      imaginary
    scales  = [] 
    offsets = [reduce((lambda v1, v2: (min(v1[0],v2[0]),min(v1[1],v2[1]))), k) for k in kernelsNormalized]
    for (k,o) in zip(kernelsNormalized, offsets):
        scale = (0.0 ,0.0)
        for v in k:
            realScale = v[0] - o[0]
            immScale  = v[1] - o[1]
            scale = (scale[0]+realScale, scale[1]+immScale)
        scales.append(scale)
            
    #print(offsets)
    #print(scales)
    finalKernels = [[(v[0],v[1],(v[0]-o[0])/s[0],(v[1]-o[1])/s[1]) for v in k] for (k,o,s) in zip(kernelsNormalized, offsets, scales)]

    componentWeights = [ (comp[2], comp[3]) for comp in P ]

    if lan=="hlsl":
        printHlsl(r, finalKernels, componentWeights, offsets, scales)
    else:
        printGlsl(r, finalKernels, componentWeights, offsets, scales)
                

def printHlsl(r, finalKernels, componentWeights, offsets, scales):
    syntax = ("uint", "float", "static const", "{", "};")
    printShaderCommon(r, finalKernels, componentWeights, offsets, scales, syntax)

def printGlsl(r, finalKernels, componentWeights, offsets, scales):
    syntax = ("int", "vec", "const", "vec4[](", ");")
    printShaderCommon(r, finalKernels, componentWeights, offsets, scales, syntax)

def printShaderCommon(r, finalKernels, componentWeights, offsets, scales, syntax):
    print("/********************************************************************/")
    print("/********************************************************************/")
    print("/*         Generated Filter by CircularDofFilterGenerator tool      */")
    print("/*     Copyright (c)     Kleber A Garcia  (kecho_garcia@hotmail.com)*/")
    print("/*       https://github.com/kecho/CircularDofFilterGenerator        */")
    print("/********************************************************************/")
    print("/********************************************************************/")
    print("/**")
    print(""" THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE. """);
    print("**/")
    diameter = r * 2 + 1; 
    print("%s %s KERNEL_RADIUS = %d;" % (syntax[2], syntax[0], r))
    print("%s %s KERNEL_COUNT = %d;" % (syntax[2], syntax[0], diameter))
    filterCount = len(finalKernels);
    for i in range(0,filterCount):
        k = finalKernels[i]
        o = offsets[i]
        s = scales[i]
        comp = componentWeights[i]
        print("%s %s4 Kernel%dBracketsRealXY_ImZW = %s4(%f,%f,%f,%f);" % (syntax[2], syntax[1],i, syntax[1], o[0],s[0],o[1],s[1]) )
        print("%s %s2 Kernel%dWeights_RealX_ImY = %s2(%f,%f);" % (syntax[2],syntax[1], i, syntax[1], comp[0],comp[1]) )
        print("%s %s4 Kernel%d_RealX_ImY_RealZ_ImW[] = %s" % (syntax[2],syntax[1], i, syntax[3]))
        for pixel in range(0,diameter):
            val = k[pixel]
            print("\t%s4(/*XY: Non Bracketed*/%f,%f,/*Bracketed WZ:*/%f,%f)%s" % (syntax[1], val[0],val[1],val[2],val[3], "," if pixel < (diameter-1) else ""))
        print("%s" % syntax[4])

def main():
    parser = argparse.ArgumentParser('Circular Dof Filter Generator. Kleber Garcia (c) 2017.\n\nPublication: http://dl.acm.org/citation.cfm?id=3085022.\nShader toy example: https://www.shadertoy.com/view/Xd2BWc\n')
    parser.add_argument('-l', dest='Language', metavar='Language', type=str, help='Language to use. Default is hlsl, possible values "hlsl" or "glsl".', choices=["hlsl","glsl"], default="hlsl");
    parser.add_argument('-r', dest='FilterRadius', metavar='FilerRadius', type=int, help='Filter Radius (in pixels). Default is 8 (diameter of 17)', default=8);
    parser.add_argument('-c', dest='Components', metavar='ComponentCount', type=int, help='Component count. Default is 2.', default=2);
    args = parser.parse_args()
    generateFilter(args.Language, args.FilterRadius, args.Components)

if __name__ == "__main__":
    main()
